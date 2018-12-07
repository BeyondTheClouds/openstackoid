with import <nixpkgs> {};
with import <nixpkgs/nixos> {};

let py = python27.withPackages (pkgs: with pkgs; [
  # These are for spacemacs python layer. To get spacemacs with the
  # correct PATH. run nix-shell, then launch Emacs inside this
  # nix-shell.
  virtualenv
]);
in stdenv.mkDerivation {
  name = "sqlalchemy-migrate";
  buildInputs = [ bashInteractive py libffi openssl luaPackages.luacheck ];
  # SHELL is overriden for whatever reason:
  # https://github.com/NixOS/nix/issues/644
  # SHELL="${bashInteractive}/bin/bash";
  ISHELL="${bashInteractive}/bin/bash";
  shellHook = ./make-env.sh;
}
