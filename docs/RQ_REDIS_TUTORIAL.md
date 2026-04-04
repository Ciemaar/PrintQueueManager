# Learning RQ & Redis for Print Queue Manager

Welcome! If you are a web developer new to asynchronous task queues, this guide will explain how **RQ** and **Redis** power the heavy lifting behind the scenes of the Print Queue Manager.

## Why Do We Need Them?

In a traditional web application, when a user makes a request, the server executes the logic and returns a response.

However, in this application, fetching data from sites like MakerWorld or Thingiverse involves spinning up a headless Playwright browser, navigating the web, and running a local Large Language Model (Llama 3.2 via Ollama) to extract data. **This can take several minutes.**

If we ran this process inside our FastAPI server, the server would hang and stop responding to users. To solve this, we use a background task queue.

## The Architecture

Our background architecture consists of three pieces:

1. **The Producer (RQ Scheduler):** A scheduler that says, "Hey, it's been a week! Go fetch new models from MakerWorld."
2. **The Broker (Redis):** A lightning-fast, in-memory database. Think of it as a waiting line (queue). When the Producer creates a task, it drops a message into Redis.
3. **The Worker (RQ Worker):** A separate Python process continuously watching Redis. When it sees a new message in the queue, it grabs the task and executes the heavy LLM Python logic without blocking the web server.

---

## Defining a Task

Let's look at how we define a background task in `src/worker/rq_worker.py`:

```python
from redis import Redis
from rq import Queue

def get_redis_connection() -> Redis:
    return Redis.from_url("redis://localhost:6379/0")

def get_queue() -> Queue:
    return Queue(connection=get_redis_connection())

def sync_makerworld():
    result = run_scraper("makerworld", "https://makerworld.com/en/user/likes")
    return result
```

Unlike some heavier frameworks, RQ does not require decorators. The tasks remain standard Python functions.

---

## Scheduling Tasks (RQ Scheduler)

We want our queue to automatically synchronize in the background so the user's dashboard is always up-to-date. We do this using **RQ Scheduler**, which acts like a `cron` job.

In `src/worker/scheduler.py`, we set up the schedule:

```python
from rq_scheduler import Scheduler
from src.worker.rq_worker import sync_makerworld, get_redis_connection

def setup_periodic_tasks():
    redis_conn = get_redis_connection()
    scheduler = Scheduler(connection=redis_conn)

    # Schedule the sync_makerworld task to run every 1 week (604800 seconds)
    scheduler.schedule(
        scheduled_time=None,
        func=sync_makerworld,
        interval=604800.0,
        repeat=None
    )
```

---

## Running the Architecture Locally

If you look at our `docker-compose.yml`, you will see three distinct services making this happen:

1. **`redis`**: Runs the official Redis database image.
2. **`worker`**: Runs the command `rq worker -u redis://redis:6379/0`. This process sits idle until tasks appear in Redis, then executes the LLM logic.
3. **`beat`**: Runs the command `python -m src.worker.scheduler && rqscheduler -u redis://redis:6379/0`. This process registers the tasks and simply drops the sync tasks into Redis every week.

### Triggering a Task Manually

If you ever need to trigger a background task manually from inside your web application or a Python shell, you can call `.enqueue()` on the queue with the task function:

```python
from src.worker.rq_worker import get_queue, sync_makerworld

# This drops the task into Redis and returns immediately!
q = get_queue()
q.enqueue(sync_makerworld)
```

By offloading this logic, our FastAPI interface remains incredibly fast and responsive, regardless of how complex the web scraping agents become.
