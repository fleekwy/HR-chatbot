import json
import os
from pathlib import Path


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

    def register_user(self, login: str) -> bool:
        """Регистрация нового пользователя"""
        with open(self.db_path, 'r+') as f:
            data = json.load(f)
            if login in data["users"]:
                return False  # Пользователь уже существует

            data["users"][login] = {
                "is_admin": False,
                "tg_id": []
            }
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        return True

    def add_session(self, login: str, tg_id: int) -> bool:
        """Добавляет tg_id в список для указанного логина"""
        try:
            # Читаем текущие данные
            with open(self.db_path, 'r') as f:
                data = json.load(f)

            # Добавляем новый tg_id в список (если его ещё нет)
            if tg_id not in data["users"][login]["tg_id"]:
                data["users"][login]["tg_id"].append(tg_id)
            else:
                return False  # ID уже существует

            # Записываем обновлённые данные
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=4)

            return True

        except Exception as e:
            print(f"Ошибка добавления tg_id: {e}")
            return False

    def is_admin(self, login: str) -> bool:
        try:
            # Читаем текущие данные
            with open(self.db_path, 'r') as f:
                data = json.load(f)
            try:
                return data["users"][login]["is_admin"]
            except Exception as e:
                print(f"Ошибка проверки на админа: {e}")
                return False

        except Exception as e:
            print(f"Ошибка проверки на админа: {e}")
            return False

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

    # def is_authenticate(self, login: str, password: str) -> bool:
    #     """Проверка логина и пароля"""
    #     try:
    #         with open(self.db_path, 'r') as f:
    #             data = json.load(f)
    #             user = data["users"].get(login)
    #
    #             if not user:
    #                 return False  # Пользователь не найден
    #
    #             return user["password_hash"] == _hash_password(password)
    #     except FileNotFoundError:
    #         return False  # Файл базы не существует

    def remove_user(self, login: str) -> list:
        """Деактивация пользователя и удаление его данных по логину"""
        try:
            # Чтение данных из файла
            with open(self.db_path, 'r') as f:
                data = json.load(f)

            # Проверка существования пользователя
            if login not in data.get("users", {}):
                return []

            # Сохраняем tg_id для возврата
            tg_id = data["users"][login]["tg_id"]

            # Удаляем пользователя по ключу-логину
            del data["users"][login]

            # Перезаписываем файл с обновлёнными данными
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=4)

            return tg_id

        except Exception as e:
            print(f"Ошибка при удалении пользователя: {e}")
            return []


# async def test(login: str, password: str):
#     auth = AuthBot()
#
#     # Регистрация нового пользователя
#     auth.register_user(login, password)
#
#     print(auth.user_exists("Daniil.Kondratyuk@waveaccess.global"))
#     print(password)
#     # Проверка авторизации
#     if auth.is_authenticate(login, password):
#         print("Авторизация успешна!")
#     else:
#         print("Неверный логин или пароль")
#
#     # # Деактивация пользователя
#     # auth.deactivate_user(login)
#
#
# if __name__ == "__main__":
#     import asyncio
#
#     asyncio.run(test(login="Daniil.Kondratyuk@waveaccess.global", password="fleekwy&09"))
