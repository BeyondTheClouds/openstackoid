# Painlessly developing Python on NixOS
# https://sid-kap.github.io/posts/2018-03-08-nix-pipenv.html

with import <nixpkgs> {};
with import <nixpkgs/nixos> {};

let manylinux1Bin = [
    which gcc binutils stdenv
  ];
  manylinux1File = writeTextDir "_manylinux.py" ''
    print("in _manylinux.py")
    manylinux1_compatible = True
  '';
in mkShell {
  buildInputs = [ bashInteractive python37 pyre pipenv manylinux1Bin libffi openssl ];
  shellHook = ''
    export PYTHONPATH=${manylinux1File.out}:''${PYTHONPATH}

    # spacemacs deps
    # pipenv install --dev python-language-server[yapf]
    # pipenv install --dev pyls-isort
    # pipenv install --dev pyls-mypy
    pipenv run pip install ipdb

    # # dev deps
    # pip install tox
    # pip install -r requirements.txt
    # pip install -r test-requirements.txt

    # Mount /bin in the tmpfs so that I can symlink bashInteractive into /bin
    # without messing my nix config
    # PROJECT_NAME="''${$PWD//\//-}"
    PROJECT_NAME="-oid"
    OVERLAY_NAME="bin-interactive-overlay$PROJECT_NAME"

    function teardown() {
      echo "INFO: umount $OVERLAY_NAME."
      sudo umount "$OVERLAY_NAME"
    }

    # teardown on CTRL+d
    trap "teardown" exit

    if ! fgrep -q '$OVERLAY_NAME on /bin' <<< $(mount -l)
    then
      echo "INFO: Make an overlayfs on /bin and link bash in /bin"
      echo "INFO: mount $OVERLAY_NAME."

      UPP_BIN="$(mktemp -d)"
      WORK_BIN="$(mktemp -d)"

      sudo mount --types overlay --options \
        lowerdir=/bin,upperdir=$UPP_BIN,workdir=$WORK_BIN \
        "$OVERLAY_NAME" /bin

      ln --symbolic --verbose ${bashInteractive}/bin/bash /bin/bash
    fi
  '';
}
