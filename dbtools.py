import datetime
import aiosqlite
from datetime import datetime, timedelta
import pytz
moscow_tz = pytz.timezone('Europe/Moscow')
async def init_db():
    async with aiosqlite.connect("db.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                text TEXT,
                keyword TEXT,
                blacklistkeyword TEXT,
                date TEXT,
                sender TEXT,
                groupTitle TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS blacklistkeywords (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                blacklistkeyword TEXT
            )
        """)
        await db.commit()
        await db.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                keyword TEXT
            )
        """)
        await db.commit()
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                user_name TEXT,
                user_chat_id TEXT
            )
        """)
        await db.commit()
        await db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY,
                group_name TEXT,
                group_id TEXT,
                add_by_userid TEXT
            )
        """)
        await db.commit()

#Функция очистки неактуальных сообщений из бд
async def clean_db():
    conn = await aiosqlite.connect('db.db')
    cursor = await conn.cursor()
    # Вычисляем дату, которая была 2 дня назад
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=2)
    # Создаем запрос для удаления строк
    query = f"DELETE FROM messages WHERE date < '{cutoff_date}'"
    # Выполняем запрос и сохраняем изменения
    await cursor.execute(query)
    await conn.commit()
    await conn.close()

#Запросы сообщений
async def insert_messages(messages, groupTitle, keyword, blacklistkeyword):
    async with aiosqlite.connect("db.db") as db:
        for message in messages:
            await db.execute("""
                INSERT INTO messages (text, keyword, blacklistkeyword, date, sender, groupTitle)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (message['text'], keyword, blacklistkeyword or "", message['date'], message['sender'], groupTitle))
        await db.commit()

#Чтение сообщений из базы данных
async def read_messages_from_db(time_range):
    now = datetime.now(moscow_tz)
    if time_range == 'day':
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'week':
        start_time = now - timedelta(days=7)
    elif time_range == 'month':
        start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError("Invalid time range")

    start_time = start_time.isoformat()
    end_time = now.isoformat()

    query = "SELECT id, text, keyword, blacklistkeyword, date, sender, groupTitle FROM messages WHERE date BETWEEN ? AND ?"
    params = [start_time, end_time]

    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

    messages = [
        {
            "id": row[0],
            "text": row[1],
            "keyword": row[2],
            "blacklistkeyword": row[3],
            "date": row[4],
            "sender": row[5],
            "groupTitle": row[6]
        }
        for row in rows
    ]

    return messages
    
#Запросы ключевых слов
async def add_keyword(user_id: int, keyword: str) -> bool:
    async with aiosqlite.connect("db.db") as db:
        try:
            await db.execute("INSERT INTO keywords (user_id, keyword) VALUES (?, ?)", (user_id, keyword))
            await db.commit()
            return True
        except Exception as e:
            print(e)
            return False

async def add_blacklistkeyword(user_id: int, blacklistkeyword: str) -> bool:
    async with aiosqlite.connect("db.db") as db:
        try:
            await db.execute("INSERT INTO blacklistkeywords (user_id, blacklistkeyword) VALUES (?, ?)", (user_id, blacklistkeyword))
            await db.commit()
            return True
        except Exception as e:
            print(e)
            return False
#Получение из бд ключевых слов конкретного пользователя
async def get_user_keywords(user_id):
    async with aiosqlite.connect("db.db") as db:
        if (user_id == 'all'):
            cursor = await db.execute("SELECT keyword FROM keywords")
        else:
            cursor = await db.execute("SELECT keyword FROM keywords WHERE user_id=?", (user_id,))
        keywords = await cursor.fetchall()
        return [k[0] for k in keywords]

async def get_user_blacklistkeywords(user_id):
    async with aiosqlite.connect("db.db") as db:
        if (user_id == 'all'):
            cursor = await db.execute("SELECT blacklistkeyword FROM blacklistkeywords")
        else:
            cursor = await db.execute("SELECT blacklistkeyword FROM blacklistkeywords WHERE user_id=?", (user_id,))
        blacklistkeywords = await cursor.fetchall()
        return [k[0] for k in blacklistkeywords]
#Удаление ключевого слова пользователя
async def remove_keyword(user_id, keyword):
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("DELETE FROM keywords WHERE user_id=? AND keyword=?", (user_id, keyword))
        await db.commit()
        return cursor.rowcount > 0

async def remove_blacklistkeyword(user_id, blacklistkeyword):
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("DELETE FROM blacklistkeywords WHERE user_id=? AND blacklistkeyword=?", (user_id, blacklistkeyword))
        await db.commit()
        return cursor.rowcount > 0
#Запросы пользователей
async def add_user(user_id, user_name, user_chat_id):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("INSERT INTO users (user_id, user_name, user_chat_id) VALUES (?, ?, ?)", (user_id, user_name, user_chat_id))
        await db.commit()

#Получение списка пользователей бота
async def get_users_list():
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT user_id, user_name, user_chat_id FROM users")
        users_list = await cursor.fetchall()
        return users_list
    
#Удаление пользователя из бд
async def remove_user(user_id, user_name):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("DELETE FROM users WHERE user_id=? AND user_name=?", (user_id, user_name))
        await db.commit()

# Запросы Групп
async def add_group(group_id, group_name, add_by_userid):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("INSERT INTO groups (group_name, group_id, add_by_userid) VALUES (?, ?, ?)", (group_name, group_id, add_by_userid))
        await db.commit()

#Получение списка групп конкретного пользователя из бд
async def get_user_group_list(user_id):
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT group_id, group_name, add_by_userid FROM groups WHERE add_by_userid = ?", (user_id,))
        group_list = await cursor.fetchall()
        return group_list
    
#Получение списка всех групп из бд  
async def get_all_group_list():
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT group_id, group_name, add_by_userid FROM groups")
        group_list = await cursor.fetchall()
        return group_list
    
async def remove_group(add_by_userid, group_id):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("DELETE FROM groups WHERE add_by_userid=? AND group_id=?", (add_by_userid, group_id))
        await db.commit()