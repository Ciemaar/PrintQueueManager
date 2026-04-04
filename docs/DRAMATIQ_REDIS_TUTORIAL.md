# Learning Dramatiq & Redis for Print Queue Manager

Welcome! If you are a web developer new to asynchronous task queues, this guide will explain how **Dramatiq** and **Redis** power the heavy lifting behind the scenes of the Print Queue Manager.

## Why Do We Need Them?

In a traditional web application, when a user makes a request, the server executes the logic and returns a response.

However, in this application, fetching data from sites like MakerWorld or Thingiverse involves spinning up a headless Playwright browser, navigating the web, and running a local Large Language Model (Llama 3.2 via Ollama) to extract data. **This can take several minutes.**

If we ran this process inside our FastAPI server, the server would hang and stop responding to users. To solve this, we use a background task queue.

## The Architecture

Our background architecture consists of three pieces:

1. **The Producer (Periodiq):** A scheduler that says, "Hey, it's been a week! Go fetch new models from MakerWorld."
2. **The Broker (Redis):** A lightning-fast, in-memory database. Think of it as a waiting line (queue). When the Producer creates a task, it drops a message into Redis.
3. **The Worker (Dramatiq):** A separate Python process continuously watching Redis. When it sees a new message in the queue, it grabs the task and executes the heavy LLM Python logic without blocking the web server.

---

## Defining a Task

Let's look at how we define a background task in `src/worker/dramatiq_app.py`:

```python
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from periodiq import PeriodiqMiddleware, cron

# 1. Connect Dramatiq to our Redis broker
redis_broker = RedisBroker(url="redis://localhost:6379/0")
redis_broker.add_middleware(PeriodiqMiddleware())
dramatiq.set_broker(redis_broker)

# 2. Define a task using the @dramatiq.actor decorator
# We also use periodiq cron to schedule the task!
@dramatiq.actor(periodic=cron("*/30 * * * *"))
def sync_makerworld():
    result = run_scraper("makerworld", "https://makerworld.com/en/user/likes")
    return result
```

By adding `@dramatiq.actor`, `sync_makerworld` is no longer just a standard Python function. It becomes a registered Dramatiq actor that can be passed to Redis and executed asynchronously.

---

## Scheduling Tasks (Periodiq)

We want our queue to automatically synchronize in the background so the user's dashboard is always up-to-date. We do this using **Periodiq**, a scheduler for Dramatiq which acts like a `cron` job.

As seen in the code block above, we use the `periodic=cron("...")` argument inside the actor decorator. Periodiq reads these decorators and automatically queues tasks into Redis on schedule.

---

## Running the Architecture Locally

If you look at our `docker-compose.yml`, you will see three distinct services making this happen:

1. **`redis`**: Runs the official Redis database image.
2. **`worker`**: Runs the command `dramatiq src.worker.dramatiq_app`. This process sits idle until tasks appear in Redis, then executes the LLM logic.
3. **`beat`**: Runs the command `periodiq src.worker.dramatiq_app`. This process simply drops the sync tasks into Redis every week based on our cron configurations.

### Triggering a Task Manually

If you ever need to trigger a background task manually from inside your web application or a Python shell, you can call `.send()` on the task function:

```python
from src.worker.dramatiq_app import sync_makerworld

# This drops the task into Redis and returns immediately!
sync_makerworld.send()
```

By offloading this logic, our FastAPI interface remains incredibly fast and responsive, regardless of how complex the web scraping agents become.
