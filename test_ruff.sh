#!/bin/bash
ruff check --fix --unsafe-fixes src/ tests/
ruff format src/ tests/
