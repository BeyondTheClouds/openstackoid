#!/usr/bin/env bash
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative
#
# Setup a tmux with two windows and starts the two OpenStack
# clouds in each windows.

tmux new-session -d -s "$TMUX_NAME" "exec /bin/bash"
tmux rename-window 'OpenStacks'
tmux send-keys 'vagrant up CloudOne' 'C-m'
tmux send-keys 'vagrant ssh CloudOne' 'C-m'
tmux select-window -t "$TMUX_NAME:0"

# Setup CloudTwo
tmux split-window -v "exec /bin/bash"
tmux send-keys 'vagrant up CloudTwo' 'C-m'
tmux send-keys 'vagrant ssh CloudTwo' 'C-m'
tmux -2 attach-session -t "$TMUX_NAME"
