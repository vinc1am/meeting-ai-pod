#!/bin/bash

# Install required libraries
pip install -r requirements.txt

cd python-client
pip install .
cd ..

# Run the server 
until python app.py; do
    echo "Server crashed with exit code $?.  Respawning.." >&2
    sleep 1
done