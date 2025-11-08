#!/bin/bash

# Database Setup Script
# This script helps set up PostgreSQL database for testing

echo "=== Database Setup ==="
echo ""

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "Docker is available. Setting up database with Docker..."
    echo ""
    
    # Create docker-compose file for database if it doesn't exist
    if [ ! -f "../docker-compose-db.yml" ]; then
        cat > ../docker-compose-db.yml << 'EOF'
services:
  db:
    image: postgres:15
    container_name: my-fastapi-db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: app_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF
        echo "Created docker-compose-db.yml"
    fi
    
    # Start database
    echo "Starting PostgreSQL database..."
    cd ..
    docker compose -f docker-compose-db.yml up -d
    echo ""
    echo "Waiting for database to be ready..."
    sleep 5
    echo "✅ Database is running!"
    echo ""
    echo "Connection details:"
    echo "  Host: localhost"
    echo "  Port: 5432"
    echo "  Database: app_db"
    echo "  User: postgres"
    echo "  Password: password"
    
else
    echo "Docker not available. Using local PostgreSQL..."
    echo ""
    
    # Check if PostgreSQL is installed
    if ! command -v psql &> /dev/null; then
        echo "❌ PostgreSQL is not installed!"
        echo "Please install PostgreSQL or use Docker."
        exit 1
    fi
    
    # Create database
    echo "Creating database..."
    createdb app_db 2>/dev/null || echo "Database might already exist"
    echo "✅ Database setup complete!"
    echo ""
    echo "Make sure your DATABASE_URL is set correctly in .env:"
    echo "  DATABASE_URL=postgresql://postgres:password@localhost:5432/app_db"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Make sure DATABASE_URL is set in .env file"
echo "2. Run: uvicorn src.main:app --reload"
echo "3. The database tables will be created automatically on first run"

