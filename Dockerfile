FROM python:3.12.3

# Set working directory
WORKDIR /app

# Install semgrep system-wide
RUN python3 -m pip install semgrep==1.109.0 --break-system-packages

# Install system dependencies, including PostgreSQL server
RUN apt-get update && apt-get install -y \
    postgresql \
    && rm -rf /var/lib/apt/lists/*

# Set up PostgreSQL directories
RUN mkdir -p /var/run/postgresql /var/lib/postgresql/data && \
    chown postgres:postgres /var/run/postgresql /var/lib/postgresql/data

# Switch to postgres user to initialize the database
USER postgres
RUN /etc/init.d/postgresql start && \
    until pg_isready; do sleep 1; done && \
    psql -c "ALTER USER postgres WITH PASSWORD 'postgres';" && \
    createdb -O postgres zerodayf && \
    /etc/init.d/postgresql stop

# Switch back to root for the app setup
USER root

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose the app port
EXPOSE 1337

# Start PostgreSQL and the app
CMD service postgresql start && uvicorn app.main:app --host 0.0.0.0 --port 1337