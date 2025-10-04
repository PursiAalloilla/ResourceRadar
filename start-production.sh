#!/bin/bash

# Start backend
echo "Starting backend..."
conda run -n aalto_defence_hackathon_server_env gunicorn --bind 0.0.0.0:5000 --workers 4 backend.app:create_app() &
BACKEND_PID=$!

# Start client-r
echo "Starting client-r..."
serve -s client-r/build -l 3000 &
CLIENT_R_PID=$!

# Start consumer-app
echo "Starting consumer-app..."
cd consumer-app && npm run preview -- --host 0.0.0.0 --port 3001 &
CONSUMER_PID=$!

# Start legal-entity-consumer-app
echo "Starting legal-entity-consumer-app..."
cd ../legal-entity-consumer-app && npm run preview -- --host 0.0.0.0 --port 3002 &
LEGAL_PID=$!

# Wait for all processes
wait $BACKEND_PID $CLIENT_R_PID $CONSUMER_PID $LEGAL_PID
