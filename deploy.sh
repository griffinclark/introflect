#!/bin/bash

set -e

echo "========================================="
echo "Setting up Firebase Functions environment..."
echo "========================================="

cd functions

if [[ ! -d "venv" ]]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Deactivating virtual environment..."
deactivate

cd ..

echo "========================================="
echo "Deploying Firebase Functions..."
echo "========================================="
firebase deploy --only functions,hosting
