#!/bin/bash

# Check if node_modules exists, if not, install dependencies
if [ ! -d "node_modules" ]; then
    echo "node_modules not found. Installing dependencies..."
    npm install || { echo "npm install failed. Exiting."; exit 1; }
fi

# Start the React development server
echo "Starting React development server..."
npm run dev
