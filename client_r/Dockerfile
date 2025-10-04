# Use Node.js 20 for consistency
FROM node:20

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm i

# Copy the rest of the source code
COPY . .

# Build the application
RUN npm run build

# Install serve to serve static files
RUN npm install -g serve

# Use Heroku-assigned port
ENV PORT=3002
EXPOSE $PORT

# Serve the built React app
CMD serve -s build -l $PORT
