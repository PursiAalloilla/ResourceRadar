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

# Use Heroku-assigned port
ENV PORT=3000
EXPOSE $PORT

# Serve built static files
CMD serve -s dist -l $PORT
