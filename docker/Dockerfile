# Base image
FROM python:3.11-slim

# Set environment variables for Poetry
ENV POETRY_VERSION=1.8.3 \
  POETRY_HOME="/opt/poetry"

# Add Poetry bin directory to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies for installing Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry using official installer script
# Ref: https://python-poetry.org/docs/#installing-with-the-official-installer
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set the working directory in the container
WORKDIR /app

# Copy the project's dependency management files (pyproject.toml and poetry.lock)
COPY pyproject.toml poetry.lock /app/

# Install dependencies defined in pyproject.toml
# --only main: Only install `tool.poetry.dependencies` in pyproject.toml, ignoring dev dependencies
# --no-interaction: Disable interactive prompts during dependency installation
# --no-ansi: Disable ANSI output to ensure plain text output for better readability
# --no-root: Do not install the root package as a dependency (useful for containerized environments)
RUN poetry install --only main --no-interaction --no-ansi --no-root

# Copy the rest of the project files to the working directory
COPY . .

# Expose port 5000 for external access
EXPOSE 5000

# Run the application
CMD ["make", "run"]
