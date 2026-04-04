# PrintQueueManager

A Local, Agentic 3D Print Queue Management System based on a local-first architecture. This system acts as a centralized dashboard aggregating 3D models from various sites (MakerWorld, Printables, etc.) and local directories using local LLMs (like Llama 3.2 via Ollama) to extract and structure data while preserving your privacy.

## Features

- **Local Inference First:** Designed to run with Ollama to ensure complete data privacy and offline capability, with flexible support for cloud providers like OpenRouter and Alibaba.
- **Agentic Scraping:** Extracts data consistently using Pydantic AI rather than brittle HTML scraping tools.
- **Local File Monitoring:** Automatically detect and add new `.stl` or `.3mf` files.
- **Streamlined UI:** Powered by FastAPI and HTMX for lightning-fast responsive updates.

## Installation and Startup

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (tested on 3.14)
- An internet connection for the first run (to pull models).

### Instructions

1. **Clone the repository:**

   ```bash
   git clone <repository_url>
   cd print-queue-manager
   ```

2. **Pull Required LLM Models (Ollama):**

   ```bash
   # Ollama starts automatically in the Docker Compose, but you need to pull the model you intend to use.
   docker compose up -d ollama
   # Wait a few seconds for ollama to start, then pull llama3.2 (or your preferred model):
   docker compose exec -it ollama ollama pull llama3.2
   ```

3. **Start the Application:**

   ```bash
   docker compose up -d --build
   ```

   For more detailed commands on stopping, viewing logs, and managing containers, see [`docs/DOCKER_GUIDE.md`](docs/DOCKER_GUIDE.md).

4. **Access the Application:**
   Open your browser and navigate to `http://localhost:8000`.

### Local Development Installation

If you prefer to run it outside Docker, we recommend using [uv](https://docs.astral.sh/uv/) for fast environment management:

```bash
# Install dependencies and sync the environment
uv sync --all-extras --dev

# Activate the virtual environment
source .venv/bin/activate

# Run commands directly (e.g. starting the FastAPI server)
uvicorn src.app.main:app --reload

# Ensure PostgreSQL and Redis are running on your host machine!
```

## Configuration & Advanced LLM Usage

By default, the application uses local inference with Ollama. However, you can configure the system to use different models for different scraping targets via a mapping in the environment.

The configuration uses a dictionary format mapping `scraper.<source>` (or `scraper.*` for a default wildcard) to a `provider:model_name` string. Supported providers include `ollama`, `openrouter`, and `alibaba`.

### Environment Variables

For security, API keys for cloud providers must be supplied securely using environment variables or a `.env` file rather than hardcoding them. The project uses `pydantic.SecretStr` under the hood to ensure secrets are not leaked in application logs or standard string representations. If you are developing locally, simply add these keys to your environment export or local `.env`:

```bash
# Optional API Keys
OPENROUTER_API_KEY="sk-or-v1-..."
ALIBABA_API_KEY="sk-..."

# Example Model Mapping
# This sets the default scraper fallback to Trinity-Large on OpenRouter,
# while instructing the makerworld scraper to use Qwen Max on Alibaba Cloud.
LLM_MODEL_MAPPING='{"scraper.*": "openrouter:arcee-ai/trinity-large-thinking", "scraper.makerworld": "alibaba:qwen-max"}'
```

Refer to `docs/USER_GUIDE.md` for usage instructions and `docs/DEV_GUIDE.md` for further development steps.
For a comprehensive look at how to run the system depending on your role (User, Operator, Developer), see the [`docs/RUN_BOOK.md`](docs/RUN_BOOK.md).
If you are new to HTMX, check out the [`docs/HTMX_TUTORIAL.md`](docs/HTMX_TUTORIAL.md) to understand how the frontend interacts with FastAPI.
If you are new to asynchronous queues, read the [`docs/CELERY_REDIS_TUTORIAL.md`](docs/CELERY_REDIS_TUTORIAL.md) to understand the background agentic scraping.
