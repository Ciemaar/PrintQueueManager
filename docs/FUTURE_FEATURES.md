# Future Features

This document outlines potential future enhancements, features, and architectural improvements for the PrintQueueManager system.

## Architectural Improvements

- **Migrate from Celery to TaskIQ or Dramatiq:** The current background task architecture uses Celery and Redis. While robust, Celery can be heavy. A migration to an async-native queue like TaskIQ or a simpler alternative like RQ/Dramatiq has been evaluated to better match our FastAPI stack.
- **WebSockets for Live Updates:** Implement WebSockets (or Server-Sent Events/SSE) on the HTMX frontend to reflect job status changes in real-time across multiple clients without requiring manual or polling refreshes.
- **Container Image Slimming:** Optimize the Docker image size by separating the heavy Playwright chromium dependencies into a specific scraper worker image instead of bundling them in the main web/API image.

## Frontend & UI Enhancements

- **Drag-and-Drop Model File Uploads:** Allow users to directly drag and drop `.stl` or `.3mf` files into the browser window, uploading them to the `watched_folder` securely instead of relying purely on the OS filesystem watchdog.
- **Advanced Filtering and Search:** Implement full-text search capabilities across `PrintJob` titles, authors, and notes, along with multi-select filtering by source platform.
- **Dark Mode Toggle:** Implement a persistent dark mode toggle that saves the user's preference in `localStorage` or as a cookie, utilizing PicoCSS's built-in dark theme.

## Integrations & Scrapers

- **Bambu Lab / MakerWorld API Integration:** While currently scraping MakerWorld using Playwright and session cookies, we should monitor for official API releases from Bambu Lab to provide a faster and more reliable integration.
- **Thingiverse OAuth App:** Register an official OAuth application with Thingiverse so users can authenticate directly via a popup rather than manually generating and pasting a Developer API Bearer Token.

## Printing Workflow

- **G-Code Generation (Slicer Integration):** Integrate with headless CLI slicers (like PrusaSlicer or BambuStudio CLI) to automatically slice incoming `.stl` files based on pre-defined material profiles and calculate accurate print timing and filament usage.
- **OctoPrint / Klipper Integration:** Connect directly to 3D printer APIs (OctoPrint, Moonraker, Bambu Network) to push jobs straight from the queue to the printer, and track live printing status directly in the dashboard.
