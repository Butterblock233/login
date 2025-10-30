login:
	uv run main.py

tidy:
	uvx ruff check --fix
	uvx ruff format
	uvx isort .