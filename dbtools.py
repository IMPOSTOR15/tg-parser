import datetime
import aiosqlite

async def init_db():
    async with aiosqlite.connect("db.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                text TEXT,
                date TEXT,
                sender TEXT,
                groupTitle TEXT
            )
        """)
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
async def insert_messages(messages, groupTitle):
    async with aiosqlite.connect("db.db") as db:
        for message in messages:
            await db.execute("""
                INSERT INTO messages (text, date, sender, groupTitle)
                VALUES (?, ?, ?, ?)
            """, (message['text'], message['date'], message['sender'], groupTitle))
        await db.commit()

#Чтение сообщений из базы данных
async def read_messages_from_db():
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT id, text, date, sender FROM messages")
        messages = await cursor.fetchall()
        return messages
    
#Запросы ключевых слов
async def add_keyword(user_id, keyword):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("INSERT INTO keywords (user_id, keyword) VALUES (?, ?)", (user_id, keyword))
        await db.commit()

#Получение из бд ключевых слов конкретного пользователя
async def get_user_keywords(user_id):
    async with aiosqlite.connect("db.db") as db:
        if (user_id == 'all'):
            cursor = await db.execute("SELECT keyword FROM keywords")
        else:
            cursor = await db.execute("SELECT keyword FROM keywords WHERE user_id=?", (user_id,))
        keywords = await cursor.fetchall()
        return [k[0] for k in keywords]
    
#Удаление ключевого слова пользователя
async def remove_keyword(user_id, keyword):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("DELETE FROM keywords WHERE user_id=? AND keyword=?", (user_id, keyword))
        await db.commit()

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
        cursor = await db.execute("SELECT group_id, group_name FROM groups WHERE add_by_userid = ?", (user_id,))
        group_list = await cursor.fetchall()
        return group_list
    
#Получение списка всех групп из бд  
async def get_all_group_list():
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT group_id, group_name, add_by_userid FROM groups")
        group_list = await cursor.fetchall()
        return group_list
    
#Удаление группы из БД
async def remove_group(add_by_userid, group_name):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("DELETE FROM groups WHERE add_by_userid=? AND group_name=?", (add_by_userid, group_name))
        await db.commit()