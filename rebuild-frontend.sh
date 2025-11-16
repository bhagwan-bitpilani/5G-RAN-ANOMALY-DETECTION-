#!/bin/bash

set -e  # Exit on any error

echo "🚀 Frontend Rebuild Script - Fixed Version"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "package.json" ] && [ ! -f "../package.json" ]; then
    log_error "package.json not found. Please run this script from the frontend directory."
    exit 1
fi

# Navigate to frontend directory if needed
if [ -f "../package.json" ]; then
    cd ..
fi

echo "1. Checking Node.js environment..."
NODE_VERSION=$(node -v 2>/dev/null || echo "none")
NPM_VERSION=$(npm -v 2>/dev/null || echo "none")

if [ "$NODE_VERSION" != "none" ]; then
    log_info "Node.js version: $NODE_VERSION"
else
    log_error "Node.js not found!"
    echo "Installing Node.js via NodeSource..."
    
    # Install Node.js 18 from NodeSource (more reliable)
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    
    # Verify installation
    node -v
    npm -v
fi

if [ "$NPM_VERSION" != "none" ]; then
    log_info "npm version: $NPM_VERSION"
else
    log_warning "npm not found, installing..."
    sudo apt-get install -y npm
fi

echo "2. Cleaning previous installations..."
# Remove node_modules and package-lock.json for clean install
rm -rf node_modules
rm -f package-lock.json
rm -f yarn.lock

echo "3. Installing dependencies..."
# Use npm ci for clean install or npm install as fallback
if [ -f "package-lock.json" ]; then
    npm ci
else
    npm install
fi

if [ $? -ne 0 ]; then
    log_error "npm install failed!"
    log_warning "Trying with --legacy-peer-deps..."
    npm install --legacy-peer-deps
fi

echo "4. Checking package.json configuration..."
# Validate package.json structure
if ! jq empty package.json 2>/dev/null; then
    log_error "package.json is invalid JSON"
    exit 1
fi

# Check if scripts exist
if ! jq -e '.scripts.build' package.json > /dev/null; then
    log_error "package.json missing build script"
    exit 1
fi

echo "5. Building the application..."
# Try building with different strategies
npm run build

if [ $? -ne 0 ]; then
    log_warning "Build failed, trying alternative approaches..."
    
    # Try with more memory
    NODE_OPTIONS="--max-old-space-size=4096" npm run build
    
    if [ $? -ne 0 ]; then
        log_warning "Build with increased memory failed, trying development build..."
        npm run build:dev || npm run build -- --mode development
    fi
fi

echo "6. Verifying build output..."
# Check if build was successful
if [ -d "dist" ]; then
    log_info "Build output found in dist/"
    ls -la dist/
elif [ -d "build" ]; then
    log_info "Build output found in build/"
    ls -la build/
else
    log_error "No build output directory found!"
    echo "Checking for any build artifacts:"
    find . -name "index.html" -o -name "*.js" -o -name "*.css" | head -10
    exit 1
fi

echo "7. Final verification..."
# Check if index.html exists in build output
if [ -f "dist/index.html" ] || [ -f "build/index.html" ]; then
    log_info "✅ Frontend build completed successfully!"
    echo "📁 Build output:"
    find . -maxdepth 2 -name "dist" -o -name "build" | xargs ls -la
else
    log_error "❌ Build completed but no index.html found!"
    exit 1
fi

echo ""
echo "🎉 Frontend rebuild completed successfully!"
echo "📦 Next steps:"
echo "   docker compose build frontend"
echo "   docker compose up frontend"
