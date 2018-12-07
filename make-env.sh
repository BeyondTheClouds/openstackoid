#!/usr/bin/env bash

# SetUp the virtual environment
if [ ! -d venv ]
then
  virtualenv --python=python2.7 venv
  source venv/bin/activate

  # spacemacs deps
  pip install ipython
  pip install ipdb
  pip install flake8
  pip install jedi
  pip install ansible-lint
  pip install service_factory

  # dev deps
  pip install tox
fi

source venv/bin/activate

emacs &

# Mount /bin in the tmpfs so that I can symlink bash into /bin
# without messing my nix config
#
# http://blog.programster.org/overlayfs/
# https://news.ycombinator.com/item?id=5024654
# E.g, protect your home:
# > mount -t overlay -o lowerdir=~/,upperdir=/tmp/tmpHOME\
# > my-overlay ~/
# - lowerdir: Files in lowerdir appear in the overlay
# - upperdir: where creation/modification are stored
# - workdir: Needs to be an empty directory on the same fs as
#   upperdir (merge of lower/upper)
# - my-overlay: Name of the overlay for latter umount (e.g. `sudo
#   umount my-overlay`)
# - Any file created or changed in overlay appear
#   in the upper dir

PROJECT_NAME="${$(pwd)//\//-}"
OVERLAY_NAME="bin-bash-overlay$PROJECT_NAME"
TMUX_NAME="tmux$PROJECT_NAME"

function teardown() {
  echo "INFO: umount $OVERLAY_NAME."
  sudo umount "$OVERLAY_NAME"
  tmux kill-session -t "$TMUX_NAME"
}

if ! fgrep -q '$OVERLAY_NAME on /bin' <<< $(mount -l)
then
  echo "INFO: Kolla/tools uses #!/bin/bash not linked in NixOS"
  echo "INFO: Make an overlayfs on /bin and link bash in /bin"
  echo "INFO: mount $OVERLAY_NAME."

  UPP_BIN="$(mktemp -d)"
  WORK_BIN="$(mktemp -d)"

  sudo mount --types overlay --options \
    lowerdir=/bin,upperdir=$UPP_BIN,workdir=$WORK_BIN \
    "$OVERLAY_NAME" /bin

  ln --symbolic --verbose /run/current-system/sw/bin/bash /bin/bash
fi

# teardown on CTRL+d
trap "teardown" exit

# Setup RegionOne
tmux new-session -d -s "$TMUX_NAME" "exec $ISHELL"
tmux rename-window 'Regions'
tmux send-keys 'source venv/bin/activate' 'C-m'
tmux send-keys 'cd RegionOne' 'C-m'
tmux send-keys 'source EnvRegionOne/admin-openrc' 'C-m'
tmux select-window -t "$TMUX_NAME:0"
# Setup RegionTwo
tmux split-window -v "exec ${ISHELL}"
tmux send-keys 'source venv/bin/activate' 'C-m'
tmux send-keys 'cd RegionTwo' 'C-m'
tmux send-keys 'source EnvRegionOne/admin-openrc' 'C-m'
tmux -2 attach-session -t "$TMUX_NAME"

