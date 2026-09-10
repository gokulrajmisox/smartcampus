# Use a lightweight python image
FROM python:3.11-slim-bookworm

# Install system dependencies needed for spatial geometry libraries (OSMnx, shapely, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy lock and project configuration files
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv sync --frozen --no-dev

# Copy application files
COPY app.py ./
COPY src/ ./src/
COPY attached_assets/ ./attached_assets/
COPY docs/ ./docs/

# Expose Streamlit default port
EXPOSE 8501

# Run Streamlit via uv
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
