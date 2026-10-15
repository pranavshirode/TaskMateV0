FROM node:20-slim

WORKDIR /app

# Copy dependency files
COPY apps/web/package.json apps/web/package-lock.json* ./

# Install dependencies
RUN npm install

# Copy application source
COPY apps/web/ .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD node -e 'fetch("http://localhost:3000").then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))'

# Run in development mode
CMD ["npm", "run", "dev"]
