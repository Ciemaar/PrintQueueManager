# User Guide: Local 3D Print Queue Manager

Welcome to the **Local 3D Print Queue Manager**. The system allows you to organize, categorize, and prioritize your upcoming 3D prints across the internet and your local machine, completely securely and natively.

## Getting Started

1. **Viewing the Queue:** Navigate to `http://localhost:8000` to view your current list of 3D models.
2. **Local Sync (Watchdog):** Any `.stl` or `.3mf` files placed inside the configured watched directory (`watched_folder/` by default) will automatically appear in your queue.
   - **Configuration:** By default, the application watches a folder named `watched_folder` located in the root of the repository. You can change this behavior by adjusting the `WATCH_DIRECTORY` environment variable, or if you are running in Docker, by changing the host volume mount in your `docker-compose.yml`. See the [Docker Guide](DOCKER_GUIDE.md) for specifics on mounting your machine's directories (like a Downloads folder) so the container can watch it!
3. **Change Status:** Use the dropdown menu in the "Status" column to categorize your print job. Options include `TO BE PRINTED`, `PRINT IN PROGRESS`, `PRINT AGAIN`, `PRINTED`, and `SKIPPED`. Setting a job to `PRINTED` will cross it out, and setting it to `SKIPPED` will dim it.
4. **Deleting Items:** If you no longer plan on printing a model, click the **Delete** button. It will immediately be removed from your dashboard.
5. **Notes:** You can add specifics about your print to the `Material Notes` (e.g. "PLA Blue") and `Timing Notes` (e.g. "2 hours") text fields. These save automatically when you finish typing.

## Cloud Platforms (MakerWorld, Printables, Thingiverse, etc)

To retrieve the models you like from cloud platforms without using official APIs, the Print Queue Manager leverages local agents running **Ollama** and **Llama 3.2**.

However, **when official APIs are available (such as for Thingiverse)**, the system prioritizes using them for perfect, structured data retrieval. You simply need to provide your `THINGIVERSE_API_TOKEN` in the environment configuration. If the token is missing, it will gracefully fall back to the local LLM scraping method.

In the background, a Celery worker routinely queries these websites. The web page HTML is provided to an agent which understands its structure, extracting the Model Title, Author, Thumbnail, and a direct URL, then importing it into your dashboard.

### Important Note on Agent Dependencies

Ensure that you have pulled the required Ollama model prior to use, as the agent defaults to `llama3.2`. If you experience blank images or unpopulated titles, verify that your Ollama server is accessible and the LLM is installed.