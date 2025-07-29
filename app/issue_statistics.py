import asyncpg


class Database:
    def __init__(self, user, password, database, host, port=5431):
        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.port = port
        self.pool = None

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user=self.user,
            password=self.password,
            database=self.database,
            host=self.host,
            port=self.port
        )

    # поменять дельтатйм на флоат
    async def save_statistics(self, question: str, answer: str, answer_time: float):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO statistics_table (question, answer, answer_time)
                VALUES ($1, $2, $3)
                """,
                question, answer, answer_time
            )

    # добавление и удаление логина пользователя
    async def add_login(self, login: str):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO login_table (login, is_admin)
                VALUES ($1, $2)
                ON CONFLICT (login) DO NOTHING
                """,
                login, False
            )

    async def remove_login(self, login: str):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                DELETE FROM login_table
                WHERE login = $1
                """,
                login
            )

    async def login_exists(self, login: str) -> bool:
        async with self.pool.acquire() as connection:
            result = await connection.fetchval(
                "SELECT 1 FROM login_table WHERE login = $1",
                login
            )
            return result is not None

    async def delete_login_with_tg_ids(self, login: str):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                # Получаем tg_id
                tg_ids = await connection.fetch(
                    "SELECT tg_id FROM sessions WHERE login = $1", login
                )

                # Удаляем логин (сессии удалятся через CASCADE)
                await connection.execute(
                    "DELETE FROM login_table WHERE login = $1", login
                )

                return [record['tg_id'] for record in tg_ids]

    # проверка на существование и что админ
    async def set_admin_status(self, login: str, admin: bool):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                UPDATE login_table
                SET is_admin = $1
                WHERE login = $2
                """,
                admin, login
            )

    async def is_user_admin(self, login: str, tg_id: int) -> bool | None:
        async with self.pool.acquire() as connection:
            result = await connection.fetchrow(
                """
                SELECT lt.is_admin
                FROM login_table lt
                JOIN sessions s ON lt.login = s.login
                WHERE lt.login = $1 AND s.tg_id = $2
                """,
                login, tg_id
            )
            if result:
                return result['is_admin']
            return None  # Логин или tg_id не найдены или не связаны

    # Функция добавления записи в sessions
    async def add_session(self, tg_id: int, login: str):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO sessions (tg_id, login)
                VALUES ($1, $2)
                ON CONFLICT (tg_id) DO NOTHING
                """,
                tg_id, login
            )

    # Функция удаления записи по tg_id
    async def remove_session(self, tg_id: int):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                DELETE FROM sessions
                WHERE tg_id = $1
                """,
                tg_id
            )
