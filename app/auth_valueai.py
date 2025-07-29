# Импорт стандартной библиотеки для работы с операционной системой
# - Взаимодействие с переменными окружения (os.getenv)
# - Работа с файловой системой
import os

# Импорт модуля логирования для записи событий и ошибок
# - Настройка уровней логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# - Вывод логов в консоль/файл
import logging

# Импорт функции для загрузки переменных окружения из .env файла
# - Автоматическая загрузка переменных в os.environ
# - Безопасное хранение чувствительных данных (логины, пароли, ключи API)
from dotenv import load_dotenv

# Импорт библиотеки для асинхронных HTTP-запросов
# - Асинхронные GET/POST/PUT/DELETE запросы
# - Поддержка сессий и connection pooling
import aiohttp

# Импорт аннотаций типов для Type Hinting
# - Улучшение читаемости кода
# - Возможность статической проверки типов (mypy)
from typing import Dict

# Импорт современного ООП-интерфейса для работы с путями файловой системы
# - Кроссплатформенная работа с путями (Windows/Linux/Mac)
# - Удобные методы для манипуляции путями
from pathlib import Path

# Определение пути к файлу .env относительно расположения текущего скрипта
env_path = Path(__file__).resolve().parent.parent / ".env"

# Загрузка переменных окружения из указанного файла
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Определение класса, который содержит логику аутентификации на ValueAI и работы с токенами
class AuthValuai:

    # Конструктор класса, инициализирует основные параметры
    def __init__(self, login: str, password: str):
        # Сохраняем логин для доступа к API
        self.login = login
        # Сохраняем пароль для доступа к API
        self.password = password
        # Базовый URL API аутентификации (должен заканчиваться слешем)
        self.base_auth_url = "https://ml-request-prod.wavea.cc/api/external/v1/"
        # Путь к файлу .env (берется из внешней переменной env_path)
        self.env_path = env_path

    # Статический метод для обновления токенов в .env файле
    @staticmethod
    async def update_env_tokens(tokens: Dict[str, str], path_env: Path) -> None:
        """Обновляет токены доступа в .env файле и окружении"""

        # Множество обязательных ключей в словаре токенов
        required_keys = {"authorization_token", "refresh_token"}

        # Проверка наличия всех обязательных ключей
        if not all(key in tokens for key in required_keys):
            # Выбрасываем исключение если каких-то ключей нет
            raise ValueError(f"Tokens must contain {required_keys}")

        # Словарь для обновления переменных окружения
        env_updates = {
            # access_token из authorization_token
            "VALUEAI_ACCESS_TOKEN": tokens["authorization_token"],
            # refresh_token сохраняем как есть
            "VALUEAI_REFRESH_TOKEN": tokens["refresh_token"]
        }

        # Проверка существования файла .env
        file_exists = path_env.exists()
        # Список для хранения строк файла
        existing_lines = []

        # Если файл существует - читаем его содержимое
        if file_exists:
            # Открываем файл на чтение
            with open(path_env, "r") as f:
                # Читаем все строки файла
                existing_lines = f.readlines()

        # Фильтруем строки, удаляя старые значения токенов
        new_lines = []
        # Проходим по всем строкам файла
        for line in existing_lines:
            # Проверяем, не начинается ли строка с обновляемых ключей
            if not any(line.strip().startswith(f"{key}=") for key in env_updates.keys()):
                # Если нет - сохраняем строку
                new_lines.append(line.strip())

        # Проверяем нужно ли добавлять перенос строки перед новыми записями
        needs_newline = bool(new_lines) and (not new_lines[-1].endswith("\n"))

        # Открываем файл на запись
        with open(path_env, "w") as f:
            # Если есть строки для сохранения
            if new_lines:
                # Записываем их, объединяя переносами строк
                f.write("\n".join(new_lines))

            # Добавляем перенос если нужно
            if needs_newline:
                f.write("\n")

            # Записываем новые значения токенов
            for key, value in env_updates.items():
                # Формат: KEY=VALUE\n
                f.write(f"{key}={value}\n")

        # Обновляем переменные окружения в текущем процессе
        os.environ.update(env_updates)

    # Метод для получения новых токенов по логину/паролю
    async def get_new_tokens(self) -> Dict[str, str]:
        # Отладочное сообщение

        # Формируем тело запроса
        payload = {
            "username": self.login,
            "password": self.password,
        }
        # Формируем URL для запроса токенов
        get_new_url = f"{self.base_auth_url}token"

        # Создаем HTTP-сессию
        async with aiohttp.ClientSession() as session:
            # Отправляем POST-запрос
            async with session.post(get_new_url, json=payload) as response:
                # Выводим статус ответа для отладки
                logger.debug(f'response.status = {response.status}')

                # Обрабатываем возможные статусы ответа
                if response.status == 400:
                    raise Exception("Bad Request: Invalid headers")
                elif response.status == 401:
                    raise Exception("Not authorized: Invalid credentials")
                elif response.status == 200:
                    # При успехе парсим JSON ответа
                    tokens = await response.json()
                    # Обновляем токены в .env
                    await self.update_env_tokens(tokens, self.env_path)
                    # Возвращаем полученные токены
                    return tokens
                else:
                    raise Exception("Unexpected server error")

    # Метод для обновления токенов с помощью refresh_token
    async def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        # Отладочное сообщение

        # Формируем URL для обновления токенов
        refresh_url = f"{self.base_auth_url}token/refresh"

        # Формируем заголовки с текущим refresh_token
        headers = {
            "Authorization": f"Bearer {refresh_token}"
        }

        # Создаем HTTP-сессию
        async with aiohttp.ClientSession() as session:
            # Отправляем POST-запрос для обновления
            async with session.post(refresh_url, headers=headers) as response:
                # Обрабатываем возможные статусы ответа
                if response.status == 400:
                    raise Exception("Bad Request: Invalid headers")
                elif response.status == 401:
                    raise Exception("Not authorized: Invalid refresh token")
                elif response.status == 200:
                    # При успехе парсим JSON ответа
                    tokens = await response.json()
                    # Обновляем токены в .env
                    await self.update_env_tokens(tokens, self.env_path)
                    # Возвращаем новые токены
                    return tokens

    # Основной метод для получения валидного токена
    async def get_valid_token(self) -> str:
        # Отладочное сообщение

        # Получаем текущие токены из переменных окружения
        access_token = os.getenv("VALUEAI_ACCESS_TOKEN")
        refresh_token = os.getenv("VALUEAI_REFRESH_TOKEN")

        # Если токены отсутствуют - получаем новые
        if not access_token or not refresh_token:
            tokens = await self.get_new_tokens()
            return tokens["authorization_token"]

        # Пробуем обновить токены
        try:
            new_tokens = await self.refresh_tokens(refresh_token)
            return new_tokens["authorization_token"]
        except (aiohttp.ClientError, KeyError) as e:
            # В случае ошибки - получаем новые токены
            # Логируем ошибку
            logging.error(f"Ошибка освежения токена: {e}", exc_info=True)
            # Параметр exc_info=True в методе logging.error()
            # включает запись полной информации об исключении (exception traceback) в лог

            # Получаем новые токены
            tokens = await self.get_new_tokens()
            return tokens["authorization_token"]
