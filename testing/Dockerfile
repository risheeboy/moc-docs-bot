FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for testing
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    npm \
    npm-audit-resolver \
    && rm -rf /var/lib/apt/lists/*

# Install pip-audit and other security tools
RUN pip install --no-cache-dir \
    pip-audit==2.6.3 \
    safety==3.0.0

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install axe-core for accessibility testing
RUN npm install -g @axe-core/cli

COPY . .

ENTRYPOINT ["python"]
CMD ["-m", "pytest"]
