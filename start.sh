#!/bin/bash
cd ~/myProjects/SpotifyWidget
source venv/bin/activate
nohup python3 spotify_server.py &> ~/SpotifyWidget/server.log &
echo "Widget server started!"