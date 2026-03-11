# Publishing to PyPI

This guide covers how to build the Print Queue Manager into a distribution package and publish it to the Python Package Index (PyPI).

## Prerequisites

Ensure you have the Python build tools installed.

```bash
python -m pip install --upgrade build twine
```

You also need an active account on [PyPI](https://pypi.org/) (or [TestPyPI](https://test.pypi.org/)) and an API token configured in your `~/.pypirc` file.

## 1. Build the Package

Before publishing, build the source distribution (`sdist`) and the built distribution (`wheel`) using the `pyproject.toml` configuration.

Run the following command from the root of the repository:

```bash
python -m build
```

This will create a `dist/` directory containing two files:
- `print_queue_manager-0.1.0.tar.gz`
- `print_queue_manager-0.1.0-py3-none-any.whl`

## 2. Test the Package locally (Optional)

It is good practice to install the wheel locally to ensure the CLI entrypoints were mapped correctly before pushing it live.

```bash
pip install dist/print_queue_manager-0.1.0-py3-none-any.whl
printqueue --help
```

## 3. Upload to PyPI

Use `twine` to securely upload the distribution files to PyPI.

```bash
python -m twine upload dist/*
```

Twine will prompt you for your username (use `__token__` if using an API token) and your password (paste the token value).

## 4. Bumping the Version

When releasing a new version, remember to update the `version = "0.1.0"` field in the `[project]` section of `pyproject.toml` before building the new distributions. Do not overwrite existing versions on PyPI.
