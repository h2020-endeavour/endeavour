#!/bin/bash
session_name="endeavour"

tmux new-session -d -s $session_name

tmux new-window -t $session_name:1 -n 'logserver' "launch.sh test-mh 1"
tmux new-window -t $session_name:2 -n 'mininet' "launch.sh test-mh 2"
tmux new-window -t $session_name:3 -n 'everythingElse' "launch.sh test-mh 3"

