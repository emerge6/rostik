import asyncio
import os
import logging
import colorlog
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def setup_logger():
    logger = logging.getLogger("GeminiAIBot")
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler("bot.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()

genai.configure(api_key=os.getenv("gemini_api_key"))
model = genai.GenerativeModel("gemini-2.0-flash-exp")
don_prompt = os.getenv("don_prompt", "")

bot = Bot(token=os.getenv("tg_token"))
dp = Dispatcher()

dialog_memory = {}

async def generate_response(prompt: str) -> str:
    logger.info("Отправка запроса")
    try:
        response = await model.generate_content_async(prompt)
        logger.info("Ответ успешно получен")
        return response.text
    except Exception as e:
        logger.exception("Ошибка при генерации ответа: %s", e)
        return "Произошла ошибка при получении ответа. Пожалуйста, попробуйте позже."

async def handle_dialog(message: types.Message):
    user_id = message.from_user.id
    user_message = message.text
    previous_dialog = dialog_memory.get(user_id, "")
    dialog_prompt = f"{don_prompt}\nПредыдущий запрос: {previous_dialog}\nЗапрос пользователя: {user_message}"
    response_text = await generate_response(dialog_prompt)
    dialog_memory[user_id] = user_message
    return response_text


@dp.message(lambda message: message.text and "ростик" in message.text.lower())
async def ask_don(message: types.Message):
    logger.info("Сообщение с упоминанием 'ростик' от ID=%s: %s", message.from_user.id, message.text)
    response_text = await handle_dialog(message)
    await message.reply(response_text)

async def main():
    logger.info("Бот запущен и ожидает команды...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

