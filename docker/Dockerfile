### Build image
FROM python:3.12-slim as build
ENV PIP_DEFAULT_TIMEOUT=100 \
  # Allow statements and log messages to immediately appear
  PYTHONUNBUFFERED=1 \
  # disable a pip version check to reduce run-time & log-spam
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  # cache is useless in docker image, so disable to reduce image size
  PIP_NO_CACHE_DIR=1 \
  POETRY_VERSION=1.3.2

WORKDIR /app

# Copy the project's dependency management files (pyproject.toml and poetry.lock)
COPY pyproject.toml poetry.lock ./

# Set environment variables for Poetry
ENV POETRY_VERSION=1.8.3 \
  POETRY_HOME="/opt/poetry"
# Add Poetry bin directory to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies for installing Poetry
RUN apt-get update && apt-get install -y --fix-missing --no-install-recommends \
  curl \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry using official installer script
# Ref: https://python-poetry.org/docs/#installing-with-the-official-installer
# hadolint ignore=DL4006
RUN curl -sSL https://install.python-poetry.org | python3 -
# Install dependencies defined in pyproject.toml
# --only main: Only install `tool.poetry.dependencies` in pyproject.toml, ignoring dev dependencies
# --no-interaction: Disable interactive prompts during dependency installation
# --no-ansi: Disable ANSI output to ensure plain text output for better readability
# --no-root: Do not install the root package as a dependency (useful for containerized environments)
RUN poetry install --only main --no-interaction --no-ansi --no-root \
  && poetry export -f requirements.txt -o requirements.txt


### Production image
FROM python:3.12-slim as production
WORKDIR /app

COPY --from=build /app/requirements.txt .
RUN set -ex \
  # Create a non-root user
  && addgroup --system --gid 1001 appgroup \
  && adduser --system --uid 1001 --gid 1001 --no-create-home appuser \
  # Upgrade the package
  && apt-get update \
  && apt-get upgrade -y \
  && apt-get install -y --no-install-recommends \
  # Tools
  vim curl wget \
  # Install libmagic for python-magic (this is needed for detecting file type)
  libmagic1

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt \
  # Clean up
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/* \
  && rm -rf /root/.cache

# Give ownership to appuser, so that appuser can write to the log files
RUN chown -R appuser:appgroup /var/log

# Copy configration file
COPY supervisord.conf /etc/supervisor/supervisord.conf

# Copy the rest of the project files to the working directory
COPY . .

# Expose port 5000 for external access
EXPOSE 8080

# Run the application
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]

USER appuser
