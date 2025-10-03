FROM denoland/deno:alpine

WORKDIR /app

COPY . .

RUN deno install --allow-scripts

EXPOSE 5173

CMD ["deno", "run", "dev", "--host"]