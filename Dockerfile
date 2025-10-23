# Multi-stage Dockerfile for mcp-arangodb-async MCP server
# Supports both stdio and HTTP transports

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
# Use pip to install the package in editable mode to get all dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir hatchling

# Copy source code
COPY mcp_arangodb_async ./mcp_arangodb_async
COPY README.md ./

# Build the package
RUN pip install --no-cache-dir .

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim AS runtime

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash mcpuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY --chown=mcpuser:mcpuser mcp_arangodb_async ./mcp_arangodb_async

# Switch to non-root user
USER mcpuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port for HTTP transport (optional, declarative)
EXPOSE 8000

# Health check
# For stdio transport: check if process is running
# For HTTP transport: check if HTTP endpoint responds
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python.*mcp_arangodb_async" > /dev/null || exit 1

# Entrypoint: Run MCP server
# Default to stdio transport (for MCP Toolkit compatibility)
# Override with CMD for HTTP transport: ["--transport", "http", "--port", "8000"]
ENTRYPOINT ["python", "-m", "mcp_arangodb_async"]
CMD []

