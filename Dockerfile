FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy project files
COPY . .

# Install dependencies using uv
RUN uv sync --frozen

# Install Playwright browsers and dependencies
RUN uv run playwright install chromium
RUN uv run playwright install-deps chromium

# Expose the default port
EXPOSE 8000

# Set headless mode for cloud
ENV HEADLESS=true

# Run the server
CMD ["uv", "run", "python", "server.py"]
