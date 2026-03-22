import asyncio
import logging

from dotenv import load_dotenv

from bot import startup


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(startup())


if __name__ == "__main__":
    main()
