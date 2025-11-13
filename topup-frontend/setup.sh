#!/bin/bash

# Topup Frontend Setup Script
# This script installs all required dependencies using pnpm

echo "Setting up Topup Frontend..."
echo ""

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null
then
    echo "Error: pnpm is not installed."
    echo "Please install pnpm first:"
    echo "  npm install -g pnpm"
    echo "  or visit: https://pnpm.io/installation"
    exit 1
fi

echo "Installing dependencies with pnpm..."
pnpm install

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Setup complete!"
    echo ""
    echo "To start the development server, run:"
    echo "  pnpm dev"
    echo ""
    echo "The application will be available at http://localhost:3000"
else
    echo ""
    echo "✗ Setup failed. Please check the error messages above."
    exit 1
fi
