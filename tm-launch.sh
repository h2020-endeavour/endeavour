#!/bin/bash
RUN_DIR=~/endeavour
SDX_DIR=~/iSDX
RIBS_DIR=$SDX_DIR/xrs/ribs
session_name="endeavour"

tmux new-session -d -s $session_name

tmux new-window -t $session_name:1 -n 'logserver' "$RUN_DIR/launch.sh test-mh 1"
tmux new-window -t $session_name:2 -n 'mininet' "$RUN_DIR/launch.sh test-mh 2"
tmux new-window -t $session_name:3 -n 'everythingElse' "$RUN_DIR/launch.sh test-mh 3"

tmux select-window -t $session_name:3
tmux attach-session -t $session_name
