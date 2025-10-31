login:
    uv run main.py

tidy:
    uvx ruff check --fix
    uvx ruff format
    uvx isort .

clean_cache:
    rm -rf **/__pycache__
