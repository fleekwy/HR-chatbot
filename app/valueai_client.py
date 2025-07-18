import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import aiohttp
from app.auth_manager import AuthManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# VALUEAI_LOGIN = os.getenv("VALUEAI_LOGIN")
# VALUEAI_PASSWORD = os.getenv("VALUEAI_PASSWORD")


class APIError(Exception):
    """Кастомное исключение для ошибок API"""
    pass


class ValueAIClient:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.base_url = "https://ml-request-prod.wavea.cc/api/external/v1/"

    async def get_headers(self) -> dict:
        """Возвращает заголовки с актуальным токеном."""
        token = await self.auth_manager.get_valid_token()
        return {
            "Authorization": f"Bearer {token}"
        }

    @retry(
        wait=wait_exponential(multiplier=0.5, min=1, max=8),
        stop=stop_after_attempt(8),
        retry=retry_if_exception_type((aiohttp.ClientError, APIError))
    )
    async def get_chat_response(self, chat_url: str, headers: dict) -> str:
        """Получает ответ из чата с повторными попытками."""
        async with aiohttp.ClientSession() as session:
            async with session.get(chat_url, headers=headers) as response:
                if response.status != 200:
                    error = await response.text()
                    raise APIError(f"Ошибка получения ответа: {error}")

                data = await response.json()
                logger.debug(f"data: {data}")

                try:
                    return data['data'][0]['text']
                except (KeyError, IndexError):
                    raise APIError("Ответ LLM не найден в истории")

    async def send_message_to_llm(self, message: str) -> str:
        """Отправляет сообщение в LLM и возвращает ответ."""
        url = f"{self.base_url}chat"
        headers = await self.get_headers()

        payload = {
            "trained_model_id": 1,
            "rag_id": 54,
            "text": message,
            "options": {
                "temperature": 0.45,
                "tokens_request_limit": 3000,
                "tokens_response_limit": 1000,
                "top_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0,
                "instructions": "Ты — HR-ассистент компании WaveAccess...",
                "top_k": 9,
                "similarity_threshold": 0.45,
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Создаем чат
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        raise APIError(f"Ошибка создания чата: {response.status}")
                    data = await response.json()
                    chat_id = data['id']
                    logger.info(f'Чат создан: {chat_id}')

                chat_url = f"{url}/{chat_id}"

                # Получаем ответ с повторными попытками
                answer = await self.get_chat_response(chat_url, headers)

                # Удаляем чат
                async with session.delete(chat_url, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f'Ошибка удаления чата: {response.status}')
                    else:
                        logger.info('Чат успешно удален')

                return answer

        except Exception as e:
            logger.error(f"Ошибка при работе с API: {str(e)}")
            raise


# async def main():
#     try:
#         # Инициализация
#         auth_manager = AuthManager(VALUEAI_LOGIN, VALUEAI_PASSWORD)
#         client = ValueAIClient(auth_manager)
#
#         # Тестовый запрос
#         question = "Какие у меня льготы как у сотрудника?"
#         answer = await client.send_message_to_llm(question)
#         print(f"Ответ на вопрос '{question}':\n{answer}")
#
#     except Exception as e:
#         logger.error(f"Ошибка в основном потоке: {str(e)}")
