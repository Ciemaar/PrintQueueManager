# User Guide: Local 3D Print Queue Manager

Welcome to the **Local 3D Print Queue Manager**. The system allows you to organize, categorize, and prioritize your upcoming 3D prints across the internet and your local machine, completely securely and natively.

## Getting Started

1. **Viewing the Queue:** Navigate to `http://localhost:8000` to view your current list of 3D models.
2. **Local Sync (Watchdog):** Any `.stl` or `.3mf` files placed inside the configured watched directory (`watched_folder/` by default) will automatically appear in your queue.
3. **Toggle Status:** Click the **Toggle** button next to a print job to mark it as either `Printed` (crossed out and green) or `Pending` (yellow).
4. **Deleting Items:** If you no longer plan on printing a model, click the **Delete** button. It will immediately be removed from your dashboard.

## Cloud Platforms (MakerWorld, Printables, etc)

To retrieve the models you like from cloud platforms without using official APIs, the Print Queue Manager leverages local agents running **Ollama** and **Llama 3.2**.

In the background, a Celery worker routinely queries these websites. The web page HTML is provided to an agent which understands its structure, extracting the Model Title, Author, Thumbnail, and a direct URL, then importing it into your dashboard.

### Important Note on Agent Dependencies

Ensure that you have pulled the required Ollama model prior to use, as the agent defaults to `llama3.2`. If you experience blank images or unpopulated titles, verify that your Ollama server is accessible and the LLM is installed.
