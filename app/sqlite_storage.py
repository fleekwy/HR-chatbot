# Импортируем тип Dict из модуля typing для аннотации типов
# (используется для указания, что user_storage будет словарем с целыми ключами и значениями UserData)
# from typing import Dict
import json
import os
import sqlite3
from pathlib import Path
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.fsm.state import State


def _serialize_state(state: State | str | None) -> str | None:
    """Преобразует объект State в строку"""
    if state is None:
        return None
    return state.state if isinstance(state, State) else str(state)


class SQLiteStorage(BaseStorage):
    def __init__(self, db_path: Path = None):
        # Если путь не указан, используем стандартное расположение (рядом с main.py)
        if db_path is None:
            # Поднимаемся на уровень выше (из app/ в корень)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = Path(base_dir) / "states.db"
        else:
            self.db_path = Path(db_path)
        self._init_db()

    async def debug_state(self, key: StorageKey):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT state, data FROM fsm_states WHERE chat_id=? AND user_id=?",
                (key.chat_id, key.user_id)
            )
            return cursor.fetchone()

    def _init_db(self):
        """Инициализация таблицы в БД"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fsm_states (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    state TEXT,
                    data TEXT,
                    PRIMARY KEY (chat_id, user_id)
                )
            """)

    async def set_state(self, key: StorageKey, state: State | str | None = None):
        serialized_state = _serialize_state(state)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO fsm_states (chat_id, user_id, state, data)
                VALUES (?, ?, ?, COALESCE(
                    (SELECT data FROM fsm_states WHERE chat_id=? AND user_id=?), '{}'
                ))
                ON CONFLICT(chat_id, user_id) DO UPDATE
                  SET state=excluded.state
            """, (
                key.chat_id, key.user_id, serialized_state,
                key.chat_id, key.user_id
            ))
            conn.commit()

    # async def delete_state(self, user_id: int) -> bool:
    #     """Удаляет запись состояния пользователя из БД по user_id.
    #     Возвращает True если запись была удалена, False если не найдена."""
    #     try:
    #         with sqlite3.connect(self.db_path) as conn:
    #             cursor = conn.cursor()
    #
    #             # Удаляем запись
    #             cursor.execute(
    #                 "DELETE FROM fsm_states WHERE user_id = ?",
    #                 (user_id,)
    #             )
    #
    #             conn.commit()
    #             return cursor.rowcount > 0  # True если были удалены строки
    #
    #     except sqlite3.Error as e:
    #         print(f"Ошибка при удалении состояния: {e}")
    #         return False

    async def get_state(self, key: StorageKey) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT state FROM fsm_states
                WHERE chat_id = ? AND user_id = ?
                """,
                (key.chat_id, key.user_id)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    async def set_data(self, key: StorageKey, data: dict):
        serialized = json.dumps(data)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO fsm_states (chat_id, user_id, state, data)
                VALUES (?, ?, COALESCE(
                    (SELECT state FROM fsm_states WHERE chat_id=? AND user_id=?), NULL
                ), ?)
                ON CONFLICT(chat_id, user_id) DO UPDATE
                  SET data=excluded.data
            """, (
                key.chat_id, key.user_id,
                key.chat_id, key.user_id,
                serialized
            ))
            conn.commit()

    async def get_data(self, key: StorageKey) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM fsm_states WHERE chat_id=? AND user_id=?",
                (key.chat_id, key.user_id)
            )
            row = cursor.fetchone()
            return json.loads(row[0]) if row and row[0] else {}

    async def update_data(self, key: StorageKey, data: dict) -> dict:
        current = await self.get_data(key)  # получаем уже сохранённые данные
        current.update(data)  # обновляем словарь
        await self.set_data(key, current)  # сохраняем обратно
        return current  # возвращаем обновлённый словарь

    async def close(self):
        pass  # SQLite автоматически управляет соединениями

# # Объявляем класс для хранения данных пользователя
# class UserData:
#     # Метод инициализации класса (конструктор)
#     def __init__(self):
#         # Создаем атрибут last_auth, изначально равный None
#         # Будет хранить datetime объекта последней успешной авторизации пользователя
#         self.last_auth = None  # Будем хранить время последней авторизации


# Создаем словарь для временного хранения данных пользователей
# Ключи - целые числа (user_id), значения - экземпляры класса UserData
# Это упрощенная замена базе данных для примера
# В реальном проекте лучше использовать Redis или БД
# user_storage: Dict[int, UserData] = {}  # Пример временного хранилища (вместо базы данных)
