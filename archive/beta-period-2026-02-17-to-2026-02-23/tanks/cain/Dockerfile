# Cain's Tank - OpenClaw Agent
# Dockerfile for isolated OpenClaw with local Ollama

FROM node:22-slim

# Install basic tools including lsof (needed by openclaw --force)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    lsof \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install OpenClaw globally
RUN npm install -g openclaw@latest

# Create workspace
WORKDIR /openclaw
RUN mkdir -p /openclaw/workspace /logs

# Copy config (will be mounted)
COPY openclaw.json /openclaw/openclaw.json

# Environment
ENV OPENCLAW_HOME=/openclaw
ENV OPENCLAW_CONFIG_PATH=/openclaw/openclaw.json
ENV NODE_ENV=production

# Don't run gateway as daemon - run in foreground for Docker
CMD ["openclaw", "gateway", "--force"]
