import logging
import os
import shutil
import subprocess

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers.callbacks import router as callbacks_router
from handlers.commands import router as commands_router
from handlers.links import router as links_router

logger = logging.getLogger(__name__)

# yt-dlp NodeJsRuntime.MIN_SUPPORTED_VERSION
_MIN_NODE = (22, 0, 0)


def _check_node_runtime() -> None:
    node = shutil.which("node")
    if not node:
        logger.warning(
            "Node.js not found in PATH — yt-dlp cannot solve YouTube JS challenges"
        )
        return
    try:
        out = subprocess.check_output(
            [node, "--version"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=5,
        ).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("Failed to run node --version: %s", exc)
        return

    # e.g. v22.17.1
    raw = out.lstrip("vV")
    try:
        parts = tuple(int(p) for p in raw.split(".")[:3])
    except ValueError:
        logger.warning("Could not parse Node.js version: %s", out)
        return

    if parts < _MIN_NODE:
        logger.warning(
            "Node.js %s is too old (need >= %s) — yt-dlp will mark it unsupported",
            out,
            ".".join(map(str, _MIN_NODE)),
        )
    else:
        logger.info("Node.js %s OK for yt-dlp", out)


async def startup() -> None:
    bot = Bot(token=os.getenv("TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(commands_router)
    dp.include_router(links_router)
    dp.include_router(callbacks_router)

    @dp.startup()
    async def on_startup() -> None:
        _check_node_runtime()
        logger.info("Start.")

    @dp.shutdown()
    async def on_shutdown() -> None:
        logger.info("Exit.")

    await dp.start_polling(bot)
