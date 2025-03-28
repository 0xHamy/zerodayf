FROM python:3.12.3

# Set working directory
WORKDIR /app

# Install semgrep system-wide
RUN python3 -m pip install semgrep==1.109.0 --break-system-packages


# Install system dependencies
RUN apt-get update && apt-get install -y \
    pandoc \
    texlive-full \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*


# Create and add wait-for script
RUN echo '#!/bin/bash\n\
until nc -z localhost 5757; do\n\
  echo "Waiting for database..."\n\
  sleep 2\n\
done\n\
echo "Database is ready!"\n\
exec "$@"' > /wait-for.sh && chmod +x /wait-for.sh

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 1337

CMD ["/wait-for.sh", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "1337"]
