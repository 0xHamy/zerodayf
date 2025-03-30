# Installation
The installation was tested on xUbuntu Linux version 24.04. It should work the same across other Ubuntu & Debian based distros but not sure about Windows. 

There are two ways to install zerodayf: 
- Docker
- Local setup


## 🛠️ Installation with Docker
Deploying Zerodayf via Docker container represents the most efficient implementation method, offering significant advantages over local installation.

To create a container, execute the following command in the Zerodayf root directory:
```bash
sudo docker-compose up --build -d
```

If you want to see the web app's logs, start without `-d` argument.

If you want to make changes and have them reflected, remove & start the container again:
```bash
sudo docker-compose down
sudo docker volume rm zerodayf_postgres_data
sudo docker-compose up --build -d
```

Upon successful execution, Zerodayf will be accessible at `127.0.0.1:1337`. 

The Docker container configuration implements the following specifications through the `Dockerfile`:
- Python 3.12.3 installation
- Installation of essential dependencies (pandoc, texlive-full, postgresql, etc.)
- Implementation of a database readiness verification script
- Port 1337 exposure for web application access


### Dockerfile Configuration
The `docker-compose.yaml` configuration file requires careful consideration due to its security implications:
- Volume configurations enable Docker to access host system files, with read-only (ro) permissions to the `/home` directory, where projects are expected to reside
- While database credentials can be modified, maintaining default values is recommended unless specifically required

This Docker-based deployment method provides the most streamlined approach to implementing Zerodayf.


## Local setup
To setup zerodayf localy, run the following commands one by one (tested on Ubuntu Linux):
```
git clone https://github.com/0xHamy/zerodayf
cd zerodayf
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt 
```

Launch the app:
```
uvicorn app.main:app --reload
```

### Depedencies 
Zerodayf uses `pandoc` for formatting PDF reports, run the following command to install them all:
```
sudo sh -c "apt update && apt install pandoc texlive-full -y"
```

This is not necessary, if you are okay with HTML & Markdown reports as most people are, you won't need this. 


## PostgreSQL database setup
To store data, zerodayf uses PostgreSQL, in `database.py`, we have the following variable:
```py
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost/zerodayf"
)
```

Run the following script to setup postgresql with user `postgres`:
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



