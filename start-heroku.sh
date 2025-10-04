#!/bin/bash

# Get port from Heroku environment variable
PORT=${PORT:-5000}

# Start backend with gunicorn
echo "Starting backend on port $PORT..."
conda run -n aalto_defence_hackathon_server_env gunicorn --bind 0.0.0.0:$PORT --workers 4 backend.app:create_app() &

# Wait a moment for backend to start
sleep 5

# Start frontend services on different ports (internal)
echo "Starting frontend services..."

# Start client-r on port 3000 (internal)
serve -s client_r/build -l 3000 &
CLIENT_R_PID=$!

# Start consumer-app on port 3001 (internal)  
cd consumer-app && npm run preview -- --host 0.0.0.0 --port 3001 &
CONSUMER_PID=$!

# Start legal-entity-consumer-app on port 3002 (internal)
cd ../legal-entity-consumer-app && npm run preview -- --host 0.0.0.0 --port 3002 &
LEGAL_PID=$!

# Wait for all processes
wait $CLIENT_R_PID $CONSUMER_PID $LEGAL_PID
