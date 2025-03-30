# Database Management Guide

## Overview
Zerodayf includes a streamlined database management script for local development and testing purposes. This utility script provides straightforward commands for creating and resetting database tables. 

The database management script is located at: `zerodayf/app/models/manage_db.py`

### Usage
You can use it by running it either with reset or create arguments to drop tables or create them:
```
python3 manage_db.py reset
python3 manage_db.py create
```

## PostgreSQL database
To store data, zerodayf uses PostgreSQL, in `database.py`, we have the following variable:
```py
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost/zerodayf"
)
```

Run the following script to setup postgresql with user postgres:
```bash
#!/bin/bash

# Exit on any error
set -e

# Update package list
echo "Updating package list..."
sudo apt update -y

# Install PostgreSQL and contrib package for additional utilities
echo "Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
echo "Starting PostgreSQL service..."
sudo systemctl start postgresql

# Enable PostgreSQL to start on boot
echo "Enabling PostgreSQL to start on boot..."
sudo systemctl enable postgresql

# Switch to the default postgres user and configure
echo "Setting up PostgreSQL user and database..."
sudo -u postgres psql <<EOF
-- Set password for the postgres user
ALTER USER postgres WITH PASSWORD 'postgres';

-- Create the zerodayf database
CREATE DATABASE zerodayf;

-- Grant all privileges on zerodayf to postgres user (optional, since postgres is superuser)
GRANT ALL PRIVILEGES ON DATABASE zerodayf TO postgres;

-- Exit psql
\q
EOF

# Verify the database creation
echo "Verifying database creation..."
sudo -u postgres psql -c "\l" | grep zerodayf

# Restart PostgreSQL to apply changes
echo "Restarting PostgreSQL service..."
sudo systemctl restart postgresql

# Check PostgreSQL status
echo "Checking PostgreSQL status..."
sudo systemctl status postgresql --no-pager

echo "PostgreSQL setup complete!"
echo "User: postgres, Password: postgres, Database: zerodayf"
echo "To connect: psql -U postgres -d zerodayf"
```

Save this as setup_db.sh, give it permissions with `chmod +x setup_db.sh` and run it: `./setup_db.sh`. 

Remember that running postgresql as postgres user is insecure in production. 

