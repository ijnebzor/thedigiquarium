#!/bin/bash
cd ${DIGIQUARIUM_HOME:-/home/ijneb/digiquarium}/mcp-server
source venv/bin/activate
python server.py
