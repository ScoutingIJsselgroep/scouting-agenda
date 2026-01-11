FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv for faster dependency installation
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY scouting_agenda/ ./scouting_agenda/
COPY sync.py .
COPY run_server.py .

# Copy config files (will be overridden by volumes)
COPY config.yaml .

# Create output directory
RUN mkdir -p output

# Expose port for server
EXPOSE 8000

# Default command: run server
CMD ["python", "run_server.py"]
