# Docker Compose Guide

The `docker-compose.yml` file is the easiest way to launch the entire Print Queue Manager stack. It orchestrates the databases, the AI inference server, and the various Python application components automatically.

## The Services

When you run Docker Compose, you are spinning up seven distinct "services" (containers):

1. **`db`**: The PostgreSQL 15 database where all your print jobs and metadata are permanently stored.
2. **`redis`**: The high-speed memory broker used by Celery to pass background tasks.
3. **`ollama`**: The local AI inference server. (Note: You still have to pull your desired model, like `llama3.2`, manually the first time).
4. **`web`**: The main FastAPI application serving the HTMX user interface on port `8000`.
5. **`worker`**: The Celery process that listens to Redis and executes the heavy LLM scraping tasks.
6. **`beat`**: The Celery scheduler that drops synchronization tasks into Redis every 30 minutes.
7. **`watchdog`**: A persistent Python process monitoring the `./watched_folder` directory on your host machine for new `.stl` or `.3mf` files.

---

## Basic Commands

### 1. Start the System
To download the required images, build the Python Dockerfile, and start all services in the background:

```bash
docker-compose up -d --build
```
*The `-d` flag runs them in detached mode, meaning you get your terminal back. The `--build` flag ensures any recent code changes are packaged into the `web`, `worker`, and `watchdog` images.*

### 2. Check the Status
To see which containers are running and their health checks:

```bash
docker-compose ps
```

### 3. View Logs
Because the system runs in the background, you might want to see what a specific service is doing (for instance, tracking a background scrape).

To see logs for *all* services, streaming live (`-f`):
```bash
docker-compose logs -f
```

To see logs for *just* the background worker:
```bash
docker-compose logs -f worker
```

To see logs for *just* the web server:
```bash
docker-compose logs -f web
```

### 4. Stop the System
When you are done, you can gracefully shut down all services:

```bash
docker-compose down
```
*(This stops the containers, but leaves your database volumes intact so your data isn't lost!)*

### 5. Pulling an Ollama Model
The first time you start the system, the Ollama server will be empty. You must pull the model that your `pydantic-ai` agent is expecting (`llama3.2` by default) into the running `ollama` container:

```bash
docker exec -it print-queue-manager-ollama-1 ollama pull llama3.2
```
*(Note: Your container name might differ slightly depending on your parent folder name. Use `docker ps` to find the exact name of the Ollama container).*
