# Use a standard Python image
FROM python:3.12-slim-bookworm

# Install uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/uv

# Set work directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using the uv binary 
# (This is very fast and ensures the venv is built for the container's OS)
RUN --mount=type=cache,target=/root/.cache/uv \
    /uv/bin/uv sync --frozen --no-install-project

# Copy the rest of the application
COPY . .

# Final sync to include project code
RUN --mount=type=cache,target=/root/.cache/uv \
    /uv/bin/uv sync --frozen

# Expose Streamlit port
EXPOSE 8501

# Place uv in PATH
ENV PATH="/app/.venv/bin:/uv/bin:$PATH"

# Default entrypoint for maximum flexibility
ENTRYPOINT ["uv", "run"]

# Default command to run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
