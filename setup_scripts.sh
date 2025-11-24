#!/bin/bash
# Make startup and shutdown scripts executable
# Run this once on Unix/Linux/Mac systems

echo "Making scripts executable..."

chmod +x startup.sh
chmod +x shutdown.sh

echo "✓ startup.sh is now executable"
echo "✓ shutdown.sh is now executable"
echo ""
echo "You can now run:"
echo "  ./startup.sh   - to start all services"
echo "  ./shutdown.sh  - to stop all services"
