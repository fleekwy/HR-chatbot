# Импорт стандартного модуля логирования для записи событий и ошибок
# Позволяет выводить сообщения разных уровней (debug, info, warning, error, critical)
import logging

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


# Класс для диалога междку клиентом бота и платформой ValueAI
class ValueAIClient:
    # Инициализация клиента с менеджером аутентификации
    def __init__(self, auth_manager: AuthValuai):
        self.auth_manager = auth_manager
        self.base_url = "https://ml-request-prod.wavea.cc/api/external/v1/"

    # Метод для получения заголовков с авторизационным токеном
    async def get_headers(self) -> dict:
        """Возвращает заголовки с актуальным токеном."""
        token = await self.auth_manager.get_valid_token()
        return {
            "Authorization": f"Bearer {token}"
        }

    # Метод с автоматическими повторными попытками при ошибках
    @retry(
        wait=wait_exponential(multiplier=2, min=1, max=10),  # Экспоненциальная задержка
        stop=stop_after_attempt(8),  # Максимум 8 попыток
        retry=retry_if_exception_type((aiohttp.ClientError, APIError))  # Повтор только для этих ошибок
    )
    async def get_chat_response(self, chat_url: str, headers: dict) -> str:
        """Получает ответ из чата с повторными попытками."""
        async with aiohttp.ClientSession() as session:  # Создаем HTTP-сессию
            async with session.get(chat_url, headers=headers) as response:  # GET-запрос
                if response.status != 200:  # Проверка статуса ответа
                    error = await response.text()  # Читаем текст ошибки
                    raise APIError(f"Ошибка получения ответа: {error}")  # Своё исключение

                data = await response.json()  # Парсим JSON-ответ
                logger.debug(f"data: {data}")  # Логируем сырые данные (уровень DEBUG)

                try:
                    return data['data'][0]['text']  # Извлекаем текст ответа LLM
                except (KeyError, IndexError):  # Обработка ошибок структуры ответа
                    raise APIError("Ответ LLM не найден в истории")

        # Основной метод для отправки сообщения в LLM
    async def send_message_to_llm(self, message: str) -> str:
        """Отправляет сообщение в LLM и возвращает ответ."""
        url = f"{self.base_url}chat"  # URL для создания чата
        headers = await self.get_headers()  # Получаем заголовки с токеном

        # Формируем тело запроса с параметрами LLM
        payload = {
            "trained_model_id": 1,  # ID модели
            "rag_id": 54,  # ID RAG-системы
            "text": message,  # Текст сообщения пользователя
            "options": {  # Параметры генерации
                "temperature": 0.45,  # Креативность ответов
                "tokens_request_limit": 3000,  # Лимит токенов запроса
                "tokens_response_limit": 1000,  # Лимит токенов ответа
                "top_p": 1,  # Параметр разнообразия
                "frequency_penalty": 0,  # Штраф за частоту
                "presence_penalty": 0,  # Штраф за повторения
                # Инструкции
                "instructions": "Ты — HR-ассистент компании WaveAccess. Следуй следующим инструкциям при"
                                "ответе: отвечай только на рабочие вопросы, связанные с работой в компании. Если вопрос"
                                "рабочий - пиши в начале 'Ответ на ваш вопрос',а сам ответ пиши внизу через две строки."
                                "Во всех остальных случаях - если вопрос не чётко сформулирован, отвечай: "
                                "'Не могу обработать данный вопрос...Пожалуйста, уточните формулировку.'",
                "top_k": 9,  # Ограничение кандидатов
                "similarity_threshold": 0.45,  # Порог схожести
            }
        }

        try:
            async with aiohttp.ClientSession() as session:  # Новая сессия
                # 1. Создаем чат (POST-запрос)
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:  # Проверка статуса
                        raise APIError(f"Ошибка создания чата: {response.status}")
                    data = await response.json()  # Читаем ответ
                    chat_id = data['id']  # Извлекаем ID чата
                    logger.info(f'Чат создан: {chat_id}')  # Логируем создание

                chat_url = f"{url}/{chat_id}"  # URL для получения ответа

                # 2. Получаем ответ с повторными попытками
                answer = await self.get_chat_response(chat_url, headers)

                # 3. Удаляем чат (DELETE-запрос)
                async with session.delete(chat_url, headers=headers) as response:
                    if response.status != 200:  # Проверка статуса
                        logger.warning(f'Ошибка удаления чата: {response.status}')
                    else:
                        logger.info('Чат успешно удален')  # Логируем удаление

                return answer  # Возвращаем ответ LLM

        except Exception as e:  # Обработка любых ошибок
            logger.error(f"Ошибка при работе с API: {str(e)}")  # Логируем ошибку
            raise  # Пробрасываем исключение дальше


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
