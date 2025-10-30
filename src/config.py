# pyright: strict
from pathlib import Path

from dotenv import dotenv_values

dotenv_path = Path(__file__).parent.parent / ".env"  # ../.env


config: dict[str, str | None] = dotenv_values(dotenv_path)

if __name__ == "__main__":
    print(config.get("USERNAME"))
    print(config.get("PASSWORD"))
