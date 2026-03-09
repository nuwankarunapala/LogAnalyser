"""Entry point for the IFS middleware log analysis RCA agent."""

from pathlib import Path


def main() -> None:
    base = Path(__file__).resolve().parent
    print(f"IFS RCA agent scaffold is ready at: {base}")


if __name__ == "__main__":
    main()
