with import <nixpkgs> {};
with import <nixpkgs/nixos> {};

mkShell {
  buildInputs = [ bashInteractive luaPackages.luacheck ];
  # SHELL is overriden for whatever reason:
  # https://github.com/NixOS/nix/issues/644
  # SHELL="${bashInteractive}/bin/bash";
  ISHELL="${bashInteractive}/bin/bash";
  shellHook = ''
    # Mount /bin in the tmpfs so that I can symlink bashInteractive into /bin
    # without messing my nix config
    # PROJECT_NAME="''${$PWD//\//-}"
    PROJECT_NAME="-oid"
    OVERLAY_NAME="bin-interactive-overlay$PROJECT_NAME"
    export TMUX_NAME="tmux$PROJECT_NAME"

    function teardown() {
      echo "INFO: umount $OVERLAY_NAME."
      sudo umount "$OVERLAY_NAME"
      tmux has-session -t "$TMUX_NAME" && tmux kill-session -t "$TMUX_NAME"
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

    ./setup-env.sh;
  '';
}
