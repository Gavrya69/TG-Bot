import os

from aiogram import Bot, Dispatcher

from handlers.callbacks import router as callbacks_router
from handlers.commands import router as commands_router
from handlers.links import router as links_router


async def startup() -> None:
    bot = Bot(token=os.getenv("TOKEN"))
    dp = Dispatcher()

    dp.include_router(commands_router)
    dp.include_router(links_router)
    dp.include_router(callbacks_router)

    @dp.startup()
    async def on_startup() -> None:
        print(f"[{__name__}] Start.")

    @dp.shutdown()
    async def on_shutdown() -> None:
        print(f"[{__name__}] Exit.")

    await dp.start_polling(bot)
