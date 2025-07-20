import json
import os
from pathlib import Path
from hashlib import sha256  # Для безопасного хранения паролей


def _hash_password(password: str) -> str:
    """Хеширование пароля для безопасного хранения"""
    return sha256(password.encode()).hexdigest()


class AuthBot:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Путь относительно расположения auth_bot.py
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = Path(base_dir) / "auth_db.json"  # Теперь точно в app/
        else:
            self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Инициализация файла с пустой базой если его нет"""
        if not self.db_path.exists():
            with open(self.db_path, 'w') as f:
                json.dump({"users": {}}, f)  # Создаем файл с пустым словарем пользователей

    def register_user(self, login: str, password: str) -> bool:
        """Регистрация нового пользователя"""
        with open(self.db_path, 'r+') as f:
            data = json.load(f)
            if login in data["users"] and data["users"][login]["is_active"]:
                return False  # Пользователь уже существует

            data["users"][login] = {
                "password_hash": _hash_password(password),
                "is_active": True
            }
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        return True

    def user_exists(self, login: str) -> bool:
        """Проверяет, существует ли пользователь с указанным логином"""
        print(f'*{login}*')
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                print(data["users"])
                return login in data["users"]
        except FileNotFoundError:
            return False

    def is_authenticate(self, login: str, password: str) -> bool:
        """Проверка логина и пароля"""
        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                user = data["users"].get(login)

                if not user or not user["is_active"]:
                    return False  # Пользователь не найден или деактивирован

                return user["password_hash"] == _hash_password(password)
        except FileNotFoundError:
            return False  # Файл базы не существует

    def deactivate_user(self, login: str) -> bool:
        """Деактивация пользователя"""
        with open(self.db_path, 'r+') as f:
            data = json.load(f)
            if login not in data["users"]:
                return False

            data["users"][login]["is_active"] = False
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        return True


async def test(login: str, password: str):
    auth = AuthBot()

    # Регистрация нового пользователя
    auth.register_user(login, password)

    print(auth.user_exists("Daniil.Kondratyuk@waveaccess.global"))
    print(password)
    # Проверка авторизации
    if auth.is_authenticate(login, password):
        print("Авторизация успешна!")
    else:
        print("Неверный логин или пароль")

    # # Деактивация пользователя
    # auth.deactivate_user(login)


if __name__ == "__main__":
    import asyncio

    asyncio.run(test(login="Daniil.Kondratyuk@waveaccess.global", password="fleekwy&09"))
