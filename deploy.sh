#!/bin/bash

# Deployment Script for Firebase Cloud Functions

# Exit on any error
set -e

# Define paths
PROJECT_ROOT=$(pwd)
FUNCTIONS_DIR="$PROJECT_ROOT/functions"
SRC_DIR="$PROJECT_ROOT/src"
TEMP_SRC_DIR="$FUNCTIONS_DIR/src"

echo "===== Starting Deployment ====="

# 1. Copy shared logic to the functions directory
echo "Copying shared logic from $SRC_DIR to $TEMP_SRC_DIR..."
cp -R "$SRC_DIR" "$TEMP_SRC_DIR"

# 2. Ensure dependencies are installed in the functions directory
echo "Installing dependencies in the functions directory..."
cd "$FUNCTIONS_DIR"
pip install -r requirements.txt --target .

# 3. Deploy the functions
echo "Deploying Firebase Cloud Functions..."
firebase deploy --only functions

# 4. Cleanup: Remove the copied src folder from functions directory
echo "Cleaning up temporary files..."
rm -rf "$TEMP_SRC_DIR"

# Return to the root directory
cd "$PROJECT_ROOT"

echo "===== Deployment Completed Successfully! ====="
