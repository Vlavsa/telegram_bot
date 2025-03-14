import asyncio
import logging
from config import API_TOKEN
from db import create_table
from utils import dp

from aiogram import Bot


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Обьект бота
bot = Bot(API_TOKEN)


async def main():

    await create_table()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
