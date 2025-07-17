import os
import logging
from aiogram import types
from aiogram.client.session import aiohttp

from auth_manager import AuthManager

VALUEAI_LOGIN = os.getenv("VALUEAI_LOGIN")  # Лучше хранить в .env
VALUEAI_PASSWORD = os.getenv("VALUEAI_PASSWORD")

# Инициализация менеджера авторизации
auth_manager = AuthManager(VALUEAI_LOGIN, VALUEAI_PASSWORD)

class ValueAIClient:
    def __init__(self, auth_manag: AuthManager):
        self.auth_manager = auth_manag
        self.base_url = "https://ml-request-prod.wavea.cc/api/external/v1/"

    async def get_headers(self) -> dict:
        """Возвращает заголовки с актуальным токеном."""
        token = await self.auth_manager.get_valid_token()
        return {
            "Authorization": f"Bearer {token}"
        }

    async def create_chat(self) -> str:
        """Создаёт новый чат."""
        url = f"{self.base_url}chats"
        headers = await self.get_headers()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                data = await response.json()
                return data["chat_id"]

    async def send_message(self, chat_id: str, message: str) -> str:
        """Отправляет сообщение в ValueAI."""
        url = f"{self.base_url}/chats/{chat_id}/messages"
        headers = await self.get_headers()
        payload = {"message": message}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                return data["response"]

    async def delete_chat(self, chat_id: str) -> bool:
        """Удаляет чат."""
        url = f"{self.base_url}/chats/{chat_id}"
        headers = await self.get_headers()
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                return response.status == 200


# Инициализация клиента ValueAI
valueai_client = ValueAIClient(auth_manager)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Задай вопрос, и я обработаю его через ValueAI.")


@dp.message_handler()
async def handle_message(message: types.Message):
    try:
        chat_id = await valueai_client.create_chat()
        response = await valueai_client.send_message(chat_id, message.text)
        await message.reply(response, parse_mode=ParseMode.MARKDOWN)
        await valueai_client.delete_chat(chat_id)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.reply("⚠️ Ошибка. Попробуйте позже.")
