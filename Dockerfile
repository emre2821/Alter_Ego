# Alter/Ego Dockerfile
# Build: docker build -t alter-ego .
# Run:   docker run -it --rm alter-ego

FROM python:3.10-slim

LABEL maintainer="emre2821"
LABEL description="Alter/Ego - Lightweight text-to-speech assistant"
LABEL version="0.1.0"

# Set working directory
WORKDIR /app

# Install system dependencies for audio support
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak \
    libespeak1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir -e .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash alterego
USER alterego

# Set default command
ENTRYPOINT ["alter-ego"]
CMD ["--help"]
