import sys

with open(".github/workflows/test.yml", "r") as f:
    content = f.read()

new_content = """name: Python Tests and Coverage

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]

    steps:
    - uses: actions/checkout@v4
    - name: Install uv and set up Python
      uses: astral-sh/setup-uv@v5
      with:
        python-version: "3.14"
        enable-cache: true
    - name: Verify uv.lock is up-to-date
      run: uv lock --locked
    - name: Install dependencies
      shell: bash
      run: |
        uv sync --all-extras --dev
        if [ "$RUNNER_OS" == "Windows" ]; then
          echo "$PWD/.venv/Scripts" >> $GITHUB_PATH
        else
          echo "$PWD/.venv/bin" >> $GITHUB_PATH
        fi
    - name: Install Playwright system dependencies
      run: |
        uv run playwright install --with-deps chromium
    - name: Run ruff check
      run: |
        uv run ruff check .
    - name: Run ruff format
      run: |
        uv run ruff format --check .
    - name: Run pyright
      run: |
        uv run pyright
    - name: Run pytest (Coverage)
      env:
        PYTHONPATH: .
      run: |
        uv run pytest tests/ --cov=src --cov-fail-under=85 --cov-report=xml
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
"""

with open(".github/workflows/test.yml", "w") as f:
    f.write(new_content)
