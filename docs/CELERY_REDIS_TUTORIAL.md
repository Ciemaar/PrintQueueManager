# Learning Celery & Redis for Print Queue Manager

Welcome! If you are a web developer new to asynchronous task queues, this guide will explain how **Celery** and **Redis** power the heavy lifting behind the scenes of the Print Queue Manager.

## Why Do We Need Them?

In a traditional web application, when a user makes a request, the server executes the logic and returns a response.

However, in this application, fetching data from sites like MakerWorld or Thingiverse involves spinning up a headless Playwright browser, navigating the web, and running a local Large Language Model (Llama 3.2 via Ollama) to extract data. **This can take several minutes.**

If we ran this process inside our FastAPI server, the server would hang and stop responding to users. To solve this, we use a background task queue.

## The Architecture

Our background architecture consists of three pieces:

1. **The Producer (Celery Beat):** A scheduler that says, "Hey, it's been a week! Go fetch new models from MakerWorld."
2. **The Broker (Redis):** A lightning-fast, in-memory database. Think of it as a waiting line (queue). When the Producer creates a task, it drops a message into Redis.
3. **The Worker (Celery):** A separate Python process continuously watching Redis. When it sees a new message in the queue, it grabs the task and executes the heavy LLM Python logic without blocking the web server.

---

## Defining a Task

Let's look at how we define a background task in `src/worker/celery_app.py`:

```python
from celery import Celery

# 1. Connect Celery to our Redis broker
celery_app = Celery("printqueue", broker="redis://localhost:6379/0")

# 2. Define a task using the @task decorator
@celery_app.task
def sync_makerworld():
    result = run_scraper("makerworld", "https://makerworld.com/en/user/likes")
    return result
```

By adding `@celery_app.task`, `sync_makerworld` is no longer just a standard Python function. It becomes a registered Celery task that can be passed to Redis and executed asynchronously.

---

## Scheduling Tasks (Celery Beat)

We want our queue to automatically synchronize in the background so the user's dashboard is always up-to-date. We do this using **Celery Beat**, which acts like a `cron` job.

In `src/worker/celery_app.py`, we hook into the configuration phase to set up a schedule:

```python
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Schedule the sync_makerworld task to run every 1800 seconds (1 week)
    sender.add_periodic_task(604800.0, sync_makerworld.s(), name='sync_makerworld_periodic')
```

*Note the `.s()` on `sync_makerworld.s()`. This creates a "Signature"—a packaged up version of the task that Celery can send over the network to Redis.*

---

## Running the Architecture Locally

If you look at our `docker-compose.yml`, you will see three distinct services making this happen:

1. **`redis`**: Runs the official Redis database image.
2. **`worker`**: Runs the command `celery -A src.worker.celery_app worker`. This process sits idle until tasks appear in Redis, then executes the LLM logic.
3. **`beat`**: Runs the command `celery -A src.worker.celery_app beat`. This process simply drops the sync tasks into Redis every week.

### Triggering a Task Manually

If you ever need to trigger a background task manually from inside your web application or a Python shell, you can call `.delay()` on the task function:

```python
from src.worker.celery_app import sync_makerworld

# This drops the task into Redis and returns immediately!
sync_makerworld.delay()
```

By offloading this logic, our FastAPI interface remains incredibly fast and responsive, regardless of how complex the web scraping agents become.
