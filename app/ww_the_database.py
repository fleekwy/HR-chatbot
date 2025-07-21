import asyncpg # работа с бд 
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

# подключение к базе данных
async def connect_db():
    return await asyncpg.create_pool(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )

# Проверка, существует ли логин
async def user_exists(pool, login: str) -> bool:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT 1 FROM authorization WHERE login = $1", login)
        return row is not None

# Проверка логина и пароля
async def is_authenticated(pool, login: str, password: str) -> bool:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT password FROM authorization WHERE login = $1", login)
        if not row:
            return False
        stored_hash = row['password']
        return bcrypt.checkpw(password.encode(), stored_hash.encode())

# Сохраняем сессию пользователя
async def save_session(pool, tg_id: int, login: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO session ("TGIdDevice", login, reg_date)
            VALUES ($1, $2, NOW())
            ON CONFLICT ("TGIdDevice") DO NOTHING
        """, tg_id, login)

# Сохраняем статистику по вопросам
async def save_question_stat(pool, question: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO statistics (question, frequency)
            VALUES ($1, 1)
            ON CONFLICT (question) DO UPDATE
            SET frequency = statistics.frequency + 1;
        """, question)
