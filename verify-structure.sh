#!/bin/bash

echo "📁 Verifying project structure..."
echo "============================================"

# Check if essential directories exist
directories=("frontend" "app" "monitoring")
for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ Directory exists: $dir"
    else
        echo "❌ Missing directory: $dir"
    fi
done

echo ""
echo "📄 Checking essential files..."
echo "============================================"

# Check essential files
essential_files=(
    "docker-compose.yml"
    "frontend/package.json"
    "frontend/Dockerfile"
    "frontend/vite.config.js"
    "frontend/src/App.js"
    "frontend/src/App.css"
    "app/Dockerfile"
    "app/requirements.txt"
    "app/main.py"
    "app/models.py"
    "monitoring/prometheus.yml"
)

for file in "${essential_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ File exists: $file"
    else
        echo "❌ Missing file: $file"
    fi
done

echo ""
echo "🔍 Checking file contents..."
echo "============================================"

# Check if key files have content
check_file_content() {
    local file=$1
    if [ -f "$file" ] && [ -s "$file" ]; then
        echo "✅ File has content: $file"
    elif [ -f "$file" ]; then
        echo "⚠️  File is empty: $file"
    else
        echo "❌ File missing: $file"
    fi
}

check_file_content "docker-compose.yml"
check_file_content "frontend/package.json"
check_file_content "app/main.py"

echo ""
echo "🐳 Checking Docker configuration..."
echo "============================================"

# Check Docker Compose file
if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
    if [ -f "docker-compose.yml" ]; then
        echo "✅ Docker Compose file exists"
        # Validate compose file syntax
        if command -v docker &> /dev/null; then
            docker compose config --quiet && echo "✅ Docker Compose file is valid"
        fi
    else
        echo "❌ Docker Compose file missing"
    fi
else
    echo "⚠️  Docker not installed"
fi

echo ""
echo "📊 Summary"
echo "============================================"
echo "Project structure verification completed!"
