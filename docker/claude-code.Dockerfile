# Dockerfile for Claude Code CLI in Turbo Container
FROM python:3.11-slim

# Install Node.js (required for Claude Code CLI)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Create workspace directory
WORKDIR /workspace

# Copy subagent configurations
COPY ./subagents /workspace/subagents
COPY ./skills /workspace/skills

# Set environment variables
ENV CLAUDE_CODE_HOME=/workspace
ENV PATH="/usr/local/bin:${PATH}"

# Expose API port
EXPOSE 9000

CMD ["python", "-m", "turbo.claude_service"]
