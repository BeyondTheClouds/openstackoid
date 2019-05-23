import pytest

from openstackoid import configuration


SIMPLE_SCOPE_VALUE = "CloudOne"


COMPOUND_SCOPE_VALUE = "CloudOne&CloudTwo"


SCOPE = {"identity": SIMPLE_SCOPE_VALUE, "image": COMPOUND_SCOPE_VALUE}


def test_get_shell_scope_empty():
    assert configuration.get_shell_scope() is None


def test_push_shell_scope_error():
    with pytest.raises(TypeError):
        configuration.push_shell_scope(SIMPLE_SCOPE_VALUE)


def test_get_shell_scope():
    configuration.push_shell_scope(SCOPE)
    assert configuration.get_shell_scope() is not None
    assert configuration.get_shell_scope() == SCOPE


def test_push_shell_scope_twice():
    alternative_scope = {"network": "CloudTwo"}
    configuration.push_shell_scope(alternative_scope)
    assert configuration.get_shell_scope() != alternative_scope
    assert configuration.get_shell_scope() == SCOPE


def test_get_execution_scope_empty():
    configuration.get_execution_scope() is None


def test_push_execution_scope_error():
    with pytest.raises(TypeError):
        configuration.push_execution_scope(None)

    with pytest.raises(ValueError):
        configuration.push_execution_scope(COMPOUND_SCOPE_VALUE)


def test_get_execution_scope():
    configuration.push_execution_scope(SIMPLE_SCOPE_VALUE)
    assert configuration.get_execution_scope() is not None
    assert configuration.get_execution_scope() == SIMPLE_SCOPE_VALUE


def test_push_execution_scope_twice():
    alternative_simple_scope_value = "CloudTwo"
    configuration.push_execution_scope(alternative_simple_scope_value)
    assert configuration.get_execution_scope() == alternative_simple_scope_value


def test___local_context():
    assert configuration._get_from_context('service_scope') is None
    assert vars(configuration.__local_context) == \
        {'shell_scope': SCOPE, 'atomic_scope': 'CloudTwo'}
