#!/bin/bash

# Backend Adaptation Verification Runner
# This script starts the backend service and runs verification tests

echo "======================================================================"
echo "Backend Adaptation Verification"
echo "======================================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: No virtual environment detected"
    echo "Attempting to activate .venv..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo "Error: .venv not found. Please activate your virtual environment."
        exit 1
    fi
fi

echo "Using Python: $(which python3)"
echo "Python version: $(python3 --version)"
echo ""

# Start backend service in background
echo "Starting backend service..."
python3 start_backend_test.py &
BACKEND_PID=$!

echo "Backend service started (PID: $BACKEND_PID)"
echo "Waiting for backend to initialize..."
sleep 3

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Error: Backend service failed to start"
    exit 1
fi

echo "Backend service is running"
echo ""

# Run verification tests
echo "Running verification tests..."
echo ""
python3 verify_backend_adaptation.py
TEST_RESULT=$?

# Cleanup: Stop backend service
echo ""
echo "Stopping backend service..."
kill $BACKEND_PID 2>/dev/null
wait $BACKEND_PID 2>/dev/null

echo "Backend service stopped"
echo ""

# Report results
if [ $TEST_RESULT -eq 0 ]; then
    echo "======================================================================"
    echo "✓ Backend adaptation verification PASSED"
    echo "======================================================================"
    exit 0
else
    echo "======================================================================"
    echo "✗ Backend adaptation verification FAILED"
    echo "======================================================================"
    exit 1
fi
