# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative


from typing import Callable, Dict, Generic, Optional, Tuple, TypeVar

import ast
import functools
import logging

from .configuration import pop_execution_scope, push_execution_scope
from .interpreter import OidInterpreter
from .utils import print_func_signature


logger = logging.getLogger(__name__)


# List of AST types used to parse a scope, others are ignored during the visit
FILTERED_KEYS = (ast.Load, ast.And, ast.Or, ast.BitOr, ast.BitAnd, ast.BitXor)


T = TypeVar("T")


class OidDispatcher(Generic[T]):
    """Dispatch a function execution to the appropriate endpoint.

    In OpenStackoïd it must be declared a simple/compound scope to parse and
    then execute a function on the endpoint[s] interpreted in such scope. In the
    case of OpenStack, for example, the scope is provided in the headers of a
    HTTP request (see `OidIntepreter`). Once the scope is identified, it is
    interpreted as a Python AST and then a function is executed according to the
    scope. If the scope is compound, the function is executed on each declared
    endpoint following the logic of the declared operator that is part of the
    declared scope. Currently two binary operators are supported '&' and '|'.

    """

    def __init__(
            self,
            interpreter: OidInterpreter,
            service_type: str,
            endpoint: str,
            func: Callable[..., T],
            bool_evl_func: Callable[..., bool],
            args_xfm_func: Callable[..., Tuple[Tuple, Dict]],
            disj_res_func: Callable[..., T],
            conj_res_func: Callable[..., T],
            *arguments, **keywords):
        """Initialize the attributes to execute a function in a target endpoint.

        :param interpreter: Instance of the scope interpreter
        :param service_type: Type of the target service declared in the scope
        :param endpoint: Name of the endpoint in which the function is executed
        :param func: Function to execute (from the `scope` decorator)
        :param bool_evl_func: Method to evaluate the truth value of the `result`
           property
        :param args_xfm_func: Method to transform the original arguments of the
           scoped function
        :param disj_res_func: Method to evaluate the binary arithmetic
           `__or__` operation of the `result` property
        :param conj_res_fun: Method to evaluate the binary arithmetic
           `__and__` operation of the `result` property

        """

        self.interpreter = interpreter
        self.service_type = service_type
        self.endpoint = endpoint
        self.func = func
        self.bool_evl_func = bool_evl_func
        self.args_xfm_func = args_xfm_func
        self.disj_res_func = disj_res_func
        self.conj_res_func = conj_res_func
        self.arguments = arguments
        self.keywords = keywords

        # Result property. It is initialized on demand only
        self._result: Optional[T] = None

    @property
    def result(self) -> Optional[T]:
        if not self._result:
            self._result = self.run_func()

        return self._result

    @result.setter
    def result(self, value) -> None:
        self._result = value

    def __bool__(self):
        return self.bool_evl_func(self)

    def __or__(self, other):
        return self.disj_res_func(self, other)

    def __and__(self, other):
        return self.conj_res_func(self, other)

    def __str__(self):
        return f"{self.endpoint}" if self.endpoint else "None"

    def run_func(self) -> Optional[T]:
        """Execute the `func` according to the target scope.

        This method performs all the logic behind the interpretation and
        dispatching the execution declared in a (execution/atomic) scope.

        """

        # 1. Process (transform) the arguments of the function to execute
        args, kwargs = self.args_xfm_func(self.interpreter, self.endpoint,
                                          *self.arguments, **self.keywords)
        execution_scope = (self.service_type, self.endpoint)

        # 2. Store the execution scope in a local context
        push_execution_scope(execution_scope)

        # helper print (read-only) decorator for logging
        func = print_func_signature(self.func)

        # 3. Execute the function with the proper attributes
        result: T = func(*args, **kwargs)

        # 4. Release (free) the scope from local context
        pop_execution_scope()
        return result


class ScopeTransformer(ast.NodeTransformer, Generic[T]):
    """AST transformer class to evaluate a simple/compound OID scope.

    An Openstackoïd scope is a valid Python expression of a given supported
    type. This expression is parsed (visited) and transformed in a
    `OidDispatcher`. Two types of expression are supported during evaluation of
    the scope, 'Name' identifiers and 'Binary Operators'. During the scope
    evaluation, execution of the method associated to the `OidDispatcher` is
    executed in order to evaluate the truth value.

    """

    def __init__(self,
                 interpreter: OidInterpreter,
                 service_type: str,
                 func: Callable[..., T],
                 bool_evl_func: Callable[..., bool],
                 args_xfm_func: Callable[..., Tuple[Tuple, Dict]],
                 disj_res_func: Callable[..., OidDispatcher],
                 conj_res_func: Callable[..., OidDispatcher],
                 *arguments, **keywords):
        """Constructor required to initalize OidDispatcher instance[s].

        It requires an interpreter object to dispatch the execution to the
        proper endpoint. It also requires the service type of the (execution)
        scope that is processed. Additionally it is required all the parameters
        to initialize an `OidDispatcher` (see documentation of the `scope`
        decorator for details).

        """

        self.interpreter = interpreter
        self.service_type = service_type
        self.func: Callable[..., T] = func
        self.bool_evl_func: Callable[..., bool] = bool_evl_func
        self.args_xfm_func: Callable[..., Tuple[Tuple, Dict]] = args_xfm_func
        self.disj_res_func: Callable[..., OidDispatcher] = disj_res_func
        self.conj_res_func: Callable[..., OidDispatcher] = conj_res_func
        self.arguments = arguments
        self.keywords = keywords

    def visit_Name(self, node):
        """Process a simple scope (tree's leaf) as a Python AST.

        :returns: A `OidDispatcher` instance representing the leaf.
        """

        logger.debug(f"Processing '{node.id}'")
        return OidDispatcher(self.interpreter,
                             self.service_type,
                             node.id,
                             self.func,
                             self.bool_evl_func,
                             self.args_xfm_func,
                             self.disj_res_func,
                             self.conj_res_func,
                             *self.arguments, **self.keywords)

    def visit_BinOp(self, node):
        """Process a compound scope (with operator[s]) as a Python AST.

        This method is recursively executed by visiting all nodes until reaches
        the leaves of the three.

        :returns: A `OidDispatcher` instance representing the result of the
            branch evaluation.

        """

        # call to the 'super' method is required for implicit recursivity
        super(ScopeTransformer, self).generic_visit(node)
        operator = "__{}__".format(node.op.__class__.__name__[3:].lower())

        # check that there is left and right side before evaluating the nodes
        if hasattr(node, "left") and hasattr(node, "right"):
            left = node.left
            right = node.right
        else:
            left = node.left if hasattr(node, 'left') else node.right
            right = OidDispatcher(None, None, lambda x: x, lambda x: False)

        result = getattr(left, operator)(right)
        logger.debug(f"Evaluation: [{result}] "
                     f"({left} {operator[2:-2]} {right})")
        return result


# Default (lambda) method for the truth evaluation of an OidDispatcher result.
default_bool_evl_func = lambda dispatcher: True if dispatcher.result else False  # noqa


# Default (lambda) method to transform the arguments of a 'scope' decorated
# function, defaults to the same varargs and kwargs of the input.
default_args_xfm_func = lambda interpreter, endpoint, *args, **kwargs: (args, kwargs)  # noqa


# Default (lambda) method to evaluate the disjunction binary operation, by
# default this method mimics the base `__or__` method behaviour
default_disj_res_func = lambda this, other: this if this else other if other else None  # noqa


# Default (lambda) method to evaluate the conjunction binary operation, by
# default this method mimics the base `__and__` method behaviour.
default_conj_res_func = lambda this, other: other if this and other else None  # noqa


def scope(interpreter: OidInterpreter,
          extr_scp_func: Callable[..., str],
          bool_evl_func: Callable[..., bool] = default_bool_evl_func,
          args_xfm_func: Callable[...,
                                  Tuple[Tuple, Dict]] = default_args_xfm_func,
          disj_res_func: Callable[..., OidDispatcher] = default_disj_res_func,
          conj_res_func: Callable[..., OidDispatcher] = default_conj_res_func):
    """Wrapper method to pass attributes to the `scope` decorator.

    Most of parameters include defaults and are required in order to create an
    instance of a `OidDispatcher`, see the documentation of its constructor for
    more details.

    :param extr_scp_func: Method to extract the scope from

    """

    def decorator(func: Callable):
        """The `scope` decorator to dispatch a request to a target endpoint.

        :param func: The scoped method

        """

        @functools.wraps(func)
        def wrapper(*arguments, **keywords):
            """Wrapper implementing the `scope` decorator business logic.

            :param arguments: varargs of the scoped method
            :param keywords: kwargs of the scoped method

            """

            # 1. Extract the scope from the provider arguments
            service_type, scope = extr_scp_func(
                interpreter, *arguments, **keywords)

            # 2. Parse the scope as an AST and evaluate the tree
            tree = ast.parse(scope, mode='eval')

            # 3. Execute the provided function to the appropriate endpoint. The
            # execution is implicit because is performed during the evaluation
            # of the scope expression
            dispatcher: OidDispatcher[T] = ScopeTransformer[T](
                interpreter,
                service_type,
                func,
                bool_evl_func,
                args_xfm_func,
                disj_res_func,
                conj_res_func,
                *arguments, **keywords).visit(tree.body)

            # 4. return the result of the execution after the truth evaluation
            return dispatcher.result if dispatcher else None
        return wrapper
    return decorator
