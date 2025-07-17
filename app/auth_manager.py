import os
from dotenv import load_dotenv
import aiohttp
from typing import Dict

load_dotenv('.env')


class AuthManager:
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.base_auth_url = "https://ml-request-prod.wavea.cc/api/external/v1/"  # Уточните URL

    @staticmethod
    async def update_env_tokens(tokens: Dict[str, str]) -> None:
        """Обновляет VALUEAI_ACCESS_TOKEN и VALUEAI_REFRESH_TOKEN в .env файле.

        Args:
            tokens: Словарь с ключами authorization_token и refresh_token

        Особенности:
            - Добавляет перенос строки перед записью, если файл не пустой
            - Сохраняет все существующие переменные, кроме обновляемых
            - Корректно обрабатывает случаи с отсутствующим .env
        """
        required_keys = {"authorization_token", "refresh_token"}
        if not all(key in tokens for key in required_keys):
            raise ValueError(f"Tokens must contain {required_keys}")

        # Подготовка новых значений
        env_updates = {
            "VALUEAI_ACCESS_TOKEN": tokens["authorization_token"],
            "VALUEAI_REFRESH_TOKEN": tokens["refresh_token"]
        }

        # Чтение существующего .env
        file_exists = os.path.exists(".env")
        existing_lines = []

        if file_exists:
            with open(".env", "r") as f:
                existing_lines = f.readlines()

        # Фильтрация старых значений
        new_lines = []
        for line in existing_lines:
            if not any(line.strip().startswith(f"{key}=") for key in env_updates.keys()):
                new_lines.append(line.strip())

        # Добавление переноса строки если файл не пустой
        needs_newline = bool(new_lines) and (not new_lines[-1].endswith("\n"))

        # Запись обновленного файла
        with open(".env", "w") as f:
            # Существующие строки
            if new_lines:
                f.write("\n".join(new_lines))

            # Добавляем перенос если нужно
            if needs_newline:
                f.write("\n")

            # Новые токены
            for key, value in env_updates.items():
                f.write(f"{key}={value}\n")

        # Обновление окружения
        os.environ.update(env_updates)

    async def get_new_tokens(self) -> Dict[str, str]:
        print('ВЫПОЛНЕНИЕ ФУНКЦИИ GET_NEW_TOKENS')
        """Получает новые токены по логину и паролю."""
        payload = {
            "username": self.login,
            "password": self.password,
        }
        get_new_url = f"{self.base_auth_url}token"
        async with aiohttp.ClientSession() as session:
            async with session.post(get_new_url, json=payload) as response:
                print(f'response.status = {response.status}')
                if response.status == 400:
                    raise Exception("Bad Request: The request headers is not in Authorization (Bearer token)")
                elif response.status == 401:
                    raise Exception("Not authorized: Error: Not Authorized")
                elif response.status == 200:
                    tokens = await response.json()
                    await self.update_env_tokens(tokens)
                    return tokens
                else:
                    raise Exception("Unexceptable mistake")


    async def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """Обновляет токены с помощью refresh_token."""
        print('ВЫПОЛНЕНИЕ ФУНКЦИИ REFRESH_TOKENS')
        """Обновляет токены через /v1/token/refresh (без тела запроса)."""
        refresh_url = f"{self.base_auth_url}token/refresh"  # Полный URL
        print(f'refresh_url = {refresh_url}')
        print(f'refresh_token = {refresh_token}')
        headers = {
            "Authorization": f"Bearer {refresh_token}"  # Передаём refresh_token в заголовке
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(refresh_url, headers=headers) as response:
                if response.status == 400:
                    raise Exception("Bad Request: The request headers is not in Authorization (Bearer token)")
                elif response.status == 401:
                    raise Exception("Not authorized: Error: Not Authorized")
                elif response.status == 200:
                    tokens = await response.json()
                    await self.update_env_tokens(tokens)
                    return tokens

    async def get_valid_token(self) -> str:
        """Возвращает валидный access_token (обновляет при необходимости)."""
        print('ВЫПОЛНЕНИЕ ФУНКЦИИ GET_VALID_TOKENS')
        access_token = os.getenv("VALUEAI_ACCESS_TOKEN")
        refresh_token = os.getenv("VALUEAI_REFRESH_TOKEN")

        print(f"auth_token = {access_token}")
        print(f'refresh_token = {refresh_token}')

        if not access_token or not refresh_token:
            tokens = await self.get_new_tokens()
            return tokens["authorization_token"]

        try:
            print('Пытаюсь освежить')
            new_tokens = await self.refresh_tokens(refresh_token)
            return new_tokens["authorization_token"]
        except Exception:
            print('Не получилось освежить')
            tokens = await self.get_new_tokens()
            return tokens["authorization_token"]


#async def test():

#    print(os.getenv("VALUEAI_LOGIN"))
#    print(os.getenv("VALUEAI_PASSWORD"))


#    # Проверка работы AuthManager
#    auth_manager = AuthManager(
#        login=os.getenv("VALUEAI_LOGIN"),
#        password=os.getenv("VALUEAI_PASSWORD")
#    )

#    print(f'auth_manager.login = {auth_manager.login}, auth_manager.password = {auth_manager.password}')

    #print("1. Получение новых токенов...")
    #new_tokens = await auth_manager.get_new_tokens()
    #print("Новые токены:", new_tokens)

    #print("\n2. Получение валидного токена...")
    #valid_token = await auth_manager.get_valid_token()
    #print("Валидный токен:", valid_token)



    #print("\n3. Обновление токенов...")
    #refreshed_tokens = await auth_manager.refresh_tokens('new_tokens["refresh_token"]')
    #print("Обновленные токены:", refreshed_tokens)


#if __name__ == "__main__":
#    import asyncio

#   asyncio.run(test())
