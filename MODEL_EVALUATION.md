# Model Evaluation

This document tracks the performance, quirks, and capabilities of specific LLMs used within the Print Queue Manager for agentic scraping and extraction tasks.

*Note for AI Agents: When testing new models or adding support for different providers, you must update this file with your findings, latency measurements, and extraction accuracy.*

## Evaluated Models

### 1. `llama3.2` (via Ollama)
- **Parameters:** ~3B
- **Hosting:** Local (Ollama)
- **Extraction Accuracy:** Moderate. Needs very clear, structured HTML. Struggles with highly obfuscated or dynamic class names if context is lost.
- **Latency:** Fast (depends entirely on local GPU, typically < 1-2 seconds per extraction).
- **Pros:** Completely free, runs locally, zero data leakage.
- **Cons:** Struggles with long, messy DOM trees.

### 2. `arcee-ai/trinity-large-thinking` (via OpenRouter)
- **Parameters:** ~400B (Sparse MoE)
- **Hosting:** Cloud (OpenRouter)
- **Extraction Accuracy:** Exceptional. As an open-weights frontier reasoning model, it parses complex and noisy HTML effortlessly. The "thinking" step drastically improves JSON structuring from unstructured text.
- **Latency:** Moderate. The initial reasoning phase adds latency, but the extraction reliability reduces the need for application-level retries.
- **Pros:** State-of-the-art open-weights model, handles massive context efficiently.
- **Cons:** Network dependency, per-token API costs.

### 3. `qwen-max` (via Alibaba Cloud Model Studio)
- **Parameters:** Unknown (Proprietary / Massive)
- **Hosting:** Cloud (Alibaba Cloud)
- **Extraction Accuracy:** Excellent. Competes with GPT-4 class models. Highly reliable at adhering to JSON schema definitions provided by Pydantic AI.
- **Latency:** Low/Moderate.
- **Pros:** Cost-effective API pricing, deep reasoning capabilities.
- **Cons:** Network dependency, requires Alibaba Cloud account.
