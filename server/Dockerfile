FROM denoland/deno:2.0

# Set working directory
WORKDIR /app

# Copy only deps first (caching)
COPY server/ ./

# Copy the rest of the server code
COPY server/ ./server
COPY database.db ./database.db

# Grant permissions for filesystem and network
CMD ["run", "--allow-net", "--allow-read", "--allow-write", "app-run.js"]