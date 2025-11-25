login:
    uv run main.py
fix:tidy
	uvx ruff check --fix
tidy:
    uvx ruff format
    uvx isort .

clean_cache:
    rm -rf **/__pycache__
