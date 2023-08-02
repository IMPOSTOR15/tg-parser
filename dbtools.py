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
                template_id INTEGER,
                user_id TEXT,
                blacklistkeyword TEXT
            )
        """)
        await db.commit()
        await db.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY,
                template_id INTEGER,
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY,
                template_name TEXT,
                user__id TEXT,
                is_select INTEGER
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
async def insert_messages(messages, groupTitle, keyword, blacklistkeyword, template_id):
    async with aiosqlite.connect("db.db") as db:
        for message in messages:
            await db.execute("""
                INSERT INTO messages (text, keyword, blacklistkeyword, date, sender, groupTitle, template_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (message['text'], keyword, blacklistkeyword or "", message['date'], message['sender'], groupTitle, template_id))
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
        
async def add_keyword_to_tamplate(user_id: int, keyword: str, template_id: int) -> bool:
    async with aiosqlite.connect("db.db") as db:
        try:
            await db.execute("INSERT INTO keywords (user_id, keyword, template_id) VALUES (?, ?, ?)", (user_id, keyword, template_id))
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
        
async def add_blacklistkeyword_to_tamplate(user_id: int, blacklistkeyword: str, template_id: int) -> bool:
    async with aiosqlite.connect("db.db") as db:
        try:
            await db.execute("INSERT INTO blacklistkeywords (user_id, blacklistkeyword, template_id) VALUES (?, ?, ?)", (user_id, blacklistkeyword, template_id))
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
#С шаблона
async def get_keywords_by_template_id(template_id: int):
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT keyword FROM keywords WHERE template_id = ?", (template_id,))
        keywords = await cursor.fetchall()
    return [keyword[0] for keyword in keywords]

async def get_stopwords_by_template_id(template_id: int):
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT blacklistkeyword FROM blacklistkeywords WHERE template_id = ?", (template_id,))
        blacklistkeywords = await cursor.fetchall()
    return [blacklistkeyword[0] for blacklistkeyword in blacklistkeywords]

#Удаление ключевого слова пользователя
async def check_keyword_in_db(user_id: int, keyword: str, template_id: int) -> bool:
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT * FROM keywords WHERE user_id = ? AND keyword = ? AND template_id = ?", (user_id, keyword, template_id))
        result = await cursor.fetchone()
    return True if result else False

async def check_blacklistkeyword_in_db(user_id: int, blacklistkeyword: str, template_id: int) -> bool:
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT * FROM blacklistkeywords WHERE user_id = ? AND blacklistkeyword = ? AND template_id = ?", (user_id, blacklistkeyword, template_id))
        result = await cursor.fetchone()
    return True if result else False

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
    
async def remove_keyword_from_template(user_id: int, keyword: str, template_id: int) -> bool:
    if not await check_keyword_in_db(user_id, keyword, template_id):
        print(f"Keyword '{keyword}' does not exist in the database.")
        return False

    async with aiosqlite.connect("db.db") as db:
        try:
            await db.execute("DELETE FROM keywords WHERE user_id = ? AND keyword = ? AND template_id = ?", (user_id, keyword, template_id))
            await db.commit()
            return True
        except Exception as e:
            print(e)
            return False

async def remove_blacklistkeyword_from_template(user_id: int, blacklistkeyword: str, template_id: int) -> bool:
    if not await check_blacklistkeyword_in_db(user_id, blacklistkeyword, template_id):
        print(f"Blacklist keyword '{blacklistkeyword}' does not exist in the database.")
        return False

    async with aiosqlite.connect("db.db") as db:
        try:
            await db.execute("DELETE FROM blacklistkeywords WHERE user_id = ? AND blacklistkeyword = ? AND template_id = ?", (user_id, blacklistkeyword, template_id))
            await db.commit()
            return True
        except Exception as e:
            print(e)
            return False

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

# Запись Группы
async def add_group(group_id, group_name, add_by_userid):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("INSERT INTO groups (group_name, group_id, add_by_userid) VALUES (?, ?, ?)", (group_name, group_id, add_by_userid))
        await db.commit()

# Запись Группы в шаблон
async def add_group_template(group_id, group_name, add_by_userid, template_id):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("INSERT INTO groups (group_name, group_id, add_by_userid, template_id) VALUES (?, ?, ?, ?)", (group_name, group_id, add_by_userid, template_id))
        await db.commit()

#Получение списка групп конкретного пользователя из бд
async def get_user_group_list(user_id):
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT group_id, group_name, add_by_userid FROM groups WHERE add_by_userid = ?", (user_id,))
        group_list = await cursor.fetchall()
        return group_list

async def get_template_group_list(template_id):
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT group_id, group_name, add_by_userid FROM groups WHERE template_id = ?", (template_id,))
        group_list = await cursor.fetchall()
        return group_list
    
#Получение списка всех групп из бд  
async def get_all_group_list():
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT group_id, group_name, add_by_userid FROM groups")
        group_list = await cursor.fetchall()
        return group_list
    
#Удалание группы пользователя
async def remove_group(add_by_userid, group_id):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("DELETE FROM groups WHERE add_by_userid=? AND group_id=?", (add_by_userid, group_id))
        await db.commit()

#Удалание группы из шаблона
async def remove_group_template(add_by_userid, group_id, template_id):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("DELETE FROM groups WHERE add_by_userid=? AND group_id=? AND template_id=?", (add_by_userid, group_id, template_id))
        await db.commit()

#Получение шапблонов пользователя
async def get_templates_by_user_id(user_id):
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT * FROM templates WHERE user__id=?", (user_id,))
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        await cursor.close()

    return [dict(zip(columns, row)) for row in rows]
    
#Добавление нового шаблона
async def add_template(template_name, user_id):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("INSERT INTO templates (template_name, user__id, is_select) VALUES (?,?,?)", (template_name, user_id, 0))
        await db.commit()
        return True

async def delete_template(template_id):
    async with aiosqlite.connect("db.db") as db:
        await db.execute("DELETE FROM templates WHERE id = ?", (template_id))
        await db.commit()
        return True
    
# Выбор шаблона (установка is_select в true)
async def select_template(user_id, template_id):
    async with aiosqlite.connect("db.db") as db:
        
        await db.execute("UPDATE templates SET is_select = 0 WHERE user__id = ?", (user_id,))
        await db.execute("UPDATE templates SET is_select = 1 WHERE user__id = ? AND id = ?", (user_id, template_id))
        await db.commit()
        return True

# Нахождение выбранного шаблона
async def find_selected_template(user_id):
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT * FROM templates WHERE user__id = ? AND is_select = 1", (user_id,))
        template = await cursor.fetchone()
        return template
    
#Поиск шаблона по айди
async def get_template_name_by_id(id):
    async with aiosqlite.connect("db.db") as db:
        cursor = await db.execute("SELECT template_name FROM templates WHERE id = ?", (id,))
        template = await cursor.fetchone()
        return template[0] if template else None