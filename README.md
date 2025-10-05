# ResourceRadar

Online examples (working till I remove the Tokens):

https://emergency-map-app-9eb97d3eafb4.herokuapp.com/
https://emergency-map-app-9eb97d3eafb4.herokuapp.com/ 
https://emergency-le-consumer-app-3e6564dcb9d6.herokuapp.com/

In case you want to run the application locally you need an containerization tool like docker compose or podman. 

## Running the App with Docker Compose

1. Make sure you have [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed.

2. In the project root directory, run:

   ```bash
   docker-compose up --build
   ```

3. The app will start and be accessible at the address specified in your `docker-compose.yml` (commonly `http://localhost:PORT`).

4. To stop the app, press `Ctrl+C` and then run:

   ```bash
   docker-compose down
   ```
