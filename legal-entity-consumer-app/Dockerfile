# Stage 1: Build
FROM node:20 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve built files
FROM node:20-slim
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist

# Heroku provides a random $PORT at runtime
ENV PORT=3001
EXPOSE $PORT

# Serve the built static files
CMD serve -s dist -l $PORT
