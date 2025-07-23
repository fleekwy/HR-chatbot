# Импорт стандартного модуля логирования для записи событий и ошибок
# Позволяет выводить сообщения разных уровней (debug, info, warning, error, critical)
import logging
from datetime import datetime

# Импорт декораторов и стратегий из библиотеки tenacity для реализации повторных попыток (retry)
# - retry: декоратор для повторного выполнения функции при ошибках
# - wait_exponential: стратегия экспоненциального увеличения задержки между попытками
# - stop_after_attempt: ограничение максимального количества попыток
# - retry_if_exception_type: условие для повторных попыток только при определенных типах исключений
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# Импорт библиотеки для асинхронных HTTP-запросов
# Позволяет делать асинхронные запросы к API/веб-сервисам
import aiohttp

# Импорт собственного класса AuthManager из модуля auth_manager
# (содержит логику аутентификации на ValueAI и работы с токенами)
from app.auth_valueai import AuthValuai

# Настройка базовой конфигурации логирования для всего приложения:
# - level=logging.INFO - устанавливает уровень логирования (INFO и выше)
# - По умолчанию выводит сообщения в консоль с форматом: "LEVEL:logger_name:message"
# - Другие доступные уровни: DEBUG, WARNING, ERROR, CRITICAL
logging.basicConfig(level=logging.INFO)

# Создание объекта логгера для текущего модуля:
# - __name__ автоматически подставляет имя текущего модуля (например "app.auth_manager")
# - Позволяет идентифицировать источник лог-сообщений
# - Лучше использовать чем logging напрямую, так как:
#   1. Позволяет индивидуально настраивать логгеры для разных модулей
#   2. Поддерживает иерархию логгеров через точку в имени (например "app" и "app.auth")
logger = logging.getLogger(__name__)


# "Ты — HR-ассистент компании WaveAccess. Следуй следующим инструкциям при ответе: "
#                                 "Если вопрос удалось распознать - выдавай найденную информацию по вопросу только на"
#                               "рабочие вопросы (Контакты HR указывай только в формате:Name.Surname@waveaccess.global,"
#                                 "Не упоминай другие контактные данные); на нерабочие вопросы отвечай: "
#                                 "«Ваш вопрос не связан с работой в компании, я не могу на него ответить. "
#                                 "Задайте рабочий вопрос.»; если вопрос подразумевает запрос конфиденциальной, "
#                               "несвязанной с пользователем информации - (пароли или данные других сотрудников и т.д.)"
#                               " - отвечай: «Я не буду отвечать на этот вопрос»; если ты не нашёл ответа на нормальный"
#                                 "рабочий вопрос - отвечай: Я не владею данной информацией... Если не удалось "
#                                 " вопрос, отвечай, то отвечай по-своему."


class APIError(Exception):
    """Кастомное исключение для ошибок API"""
    pass


class ValueAIClient:
    def __init__(self, auth_manager: AuthValuai):
        self.auth_manager = auth_manager
        self.base_url = "https://ml-request-prod.wavea.cc/api/external/v1/"

    async def get_headers(self) -> dict:
        start = datetime.now()
        token = await self.auth_manager.get_valid_token()
        end = datetime.now()
        duration = round((end - start).total_seconds(), 3)
        logger.info(f"[PROFILING] get_headers: {duration} сек.")
        return {
            "Authorization": f"Bearer {token}"
        }

    @retry(
        wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type((aiohttp.ClientError, APIError))
    )
    async def get_chat_response(self, chat_url: str, headers: dict) -> str:
        start = datetime.now()

        async with aiohttp.ClientSession() as session:
            async with session.get(chat_url, headers=headers) as response:
                if response.status != 200:
                    error = await response.text()
                    raise APIError(f"Ошибка получения ответа: {error}")
                data = await response.json()
                logger.debug(f"data: {data}")
                try:
                    result = data['data'][0]['text']
                except (KeyError, IndexError):
                    raise APIError("Ответ LLM не найден в истории")

        end = datetime.now()
        duration = round((end - start).total_seconds(), 3)
        logger.info(f"[PROFILING] get_chat_response: {duration} сек. URL: {chat_url}")

        return result

    async def send_message_to_llm(self, message: str) -> str:
        # Профилирование времени
        timers = {
            'start': datetime.now(),
        }

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
                "instructions": "Ты — HR-ассистент WaveAccess. Отвечай только чётко-сформулированные вопросы. "
                                "На рабочие вопросы ответ начни с «Код ответа — 200», "
                                "через 1 абзац дай информацию. Если вопрос рабочий, но ответа нет — начина также с "
                                "«Код ответа — 200» а через 1 абзац верни: «Данные не найдены. Уточните у HR» и "
                                "дай контакты HR. Контакты указывай строго в формате Name.Surname@waveaccess.global. "
                                "На нерабочие или плохо сформулированные запросы отвечай: в начале пиши «Код "
                                "ответа — 100» а через абзац - «Нерабочий вопрос. Пожалуйста, переформулируйте». "
                                "Если дан непонятный набор символов - пиши «Вопрос неясен. Переформулируйте, "
                                "указав контекст»",
                "top_k": 9,
                "similarity_threshold": 0.45,
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                # 1. Создание чата
                timers['create_chat_start'] = datetime.now()
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        raise APIError(f"Ошибка создания чата: {response.status}")
                    data = await response.json()
                    chat_id = data['id']
                    logger.info(f'Чат создан: {chat_id}')
                timers['create_chat_end'] = datetime.now()

                # 2. Получение ответа
                timers['get_response_start'] = datetime.now()
                chat_url = f"{url}/{chat_id}"
                answer = await self.get_chat_response(chat_url, headers)
                timers['get_response_end'] = datetime.now()

                # 3. Удаление чата
                timers['delete_chat_start'] = datetime.now()
                async with session.delete(chat_url, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f'Ошибка удаления чата: {response.status}')
                    else:
                        logger.info('Чат успешно удален')
                timers['delete_chat_end'] = datetime.now()

                # 4. Конец
                timers['end'] = datetime.now()

                # Печать профилирования
                total = (timers['end'] - timers['start']).total_seconds()
                create_chat = (timers['create_chat_end'] - timers['create_chat_start']).total_seconds()
                get_response = (timers['get_response_end'] - timers['get_response_start']).total_seconds()
                delete_chat = (timers['delete_chat_end'] - timers['delete_chat_start']).total_seconds()

                print("\n=== Профилирование send_message_to_llm ===")
                print(f"1. Создание чата: {create_chat:.2f} сек. ({create_chat/total*100:.1f}%)")
                print(f"2. Получение ответа: {get_response:.2f} сек. ({get_response/total*100:.1f}%)")
                print(f"3. Удаление чата: {delete_chat:.2f} сек. ({delete_chat/total*100:.1f}%)")
                print(f"4. Общее время: {total:.2f} сек.")
                print("==========================================\n")

                return answer

        except Exception as e:
            logger.error(f"Ошибка при работе с API: {str(e)}")
            raise


# Функция для тестироания
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
