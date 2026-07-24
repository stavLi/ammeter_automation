FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY . .

# Default: run the test suite. Override the command to run the emulators instead
# (see docker-compose.yml, which runs `python main.py` as a long-lived service).
CMD ["pytest", "-q"]
