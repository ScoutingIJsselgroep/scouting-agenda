FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv for faster dependency installation
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Copy application code (needed for installation)
COPY scouting_agenda/ ./scouting_agenda/

# Install package with dependencies (this creates the scripts)
RUN uv pip install --system --no-cache .

# Copy config files (will be overridden by volumes)
COPY config.yaml .

# Create output directory
RUN mkdir -p output

# Expose port for server
EXPOSE 8000

# Default command: run server
CMD ["server"]
