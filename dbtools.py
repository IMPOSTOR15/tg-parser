import os
import asyncpg
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import asyncio

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
moscow_tz = pytz.timezone('Europe/Moscow')

DATABASE_URL = os.getenv("DATABASE_URL")


async def create_pool():
    global POOL
    POOL = await asyncpg.create_pool(DATABASE_URL)


async def get_pool_connection():
    return POOL.acquire()


class PoolConnection:
    async def __aenter__(self):
        self.conn = await POOL.acquire()
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await POOL.release(self.conn)


async def init_db():
    async with PoolConnection() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                text TEXT,
                keyword TEXT,
                blacklistkeyword TEXT,
                date TEXT,
                sender TEXT,
                groupTitle TEXT,
                senderId TEXT,
                template_id INTEGER
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blacklistkeywords (
                id SERIAL PRIMARY KEY,
                template_id INTEGER,
                user_id TEXT,
                blacklistkeyword TEXT
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id SERIAL PRIMARY KEY,
                template_id INTEGER,
                user_id TEXT,
                keyword TEXT
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                user_name TEXT,
                user_chat_id TEXT
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id SERIAL PRIMARY KEY,
                group_name TEXT,
                group_id TEXT,
                add_by_userid TEXT,
                template_id INTEGER,
                link TEXT
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id SERIAL PRIMARY KEY,
                template_name TEXT,
                user__id TEXT,
                is_select INTEGER
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blacklist_senders (
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                template_id TEXT,
                sender_name TEXT
            )
        """)


async def clean_db():
    async with PoolConnection() as conn:
        cutoff_date = (datetime.now() - timedelta(days=2)).isoformat()
        await conn.execute(f"DELETE FROM messages WHERE date < $1", cutoff_date)


async def insert_messages(messages, groupTitle, keyword, blacklistkeyword, template_id, senderId):
    async with PoolConnection() as conn:
        for message in messages:
            await conn.execute("""
                INSERT INTO messages (text, keyword, blacklistkeyword, date, sender, groupTitle, template_id, senderId)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, message['text'], keyword, blacklistkeyword or "", message['date'], message['sender'], groupTitle, template_id, senderId)


async def read_messages_from_db(time_range):
    async with PoolConnection() as conn:
        now = datetime.now(moscow_tz)
        if time_range == 'day':
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'week':
            start_time = now - timedelta(days=7)
        elif time_range == 'month':
            start_time = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            raise ValueError("Invalid time range")

        query = "SELECT id, text, keyword, blacklistkeyword, date, sender, groupTitle FROM messages WHERE date BETWEEN $1 AND $2"
        rows = await conn.fetch(query, start_time, now)

        messages = [
            {
                "id": row['id'],
                "text": row['text'],
                "keyword": row['keyword'],
                "blacklistkeyword": row['blacklistkeyword'],
                "date": row['date'],
                "sender": row['sender'],
                "groupTitle": row['groupTitle']
            }
            for row in rows
        ]
        return messages


async def fetch_messages_by_sender_id(sender_id):
    async with PoolConnection() as conn:
        try:
            # Выбираем все сообщения пользователя с данным sender_id
            records = await conn.fetch("""
                SELECT date, text FROM messages WHERE senderId = $1
            """, sender_id)

            # Преобразовываем каждую запись в кортеж (date, text)
            result = [(record["text"], record["date"]) for record in records]

            return result
        except Exception as e:
            print(f"Error: {e}")
            return []


async def add_keyword(user_id: int, keyword: str) -> bool:
    async with PoolConnection() as conn:
        try:
            await conn.execute("INSERT INTO keywords (user_id, keyword) VALUES ($1, $2)", user_id, keyword)
            return True
        except:
            return False


async def add_keyword_to_tamplate(user_id: int, keyword: str, template_id: int) -> bool:
    async with PoolConnection() as conn:
        try:
            await conn.execute("INSERT INTO keywords (user_id, keyword, template_id) VALUES ($1, $2, $3)", user_id, keyword, template_id)
            return True
        except Exception as e:
            print(f"Failed to add sender to blacklist. Error: {e}")
            return False


async def add_sender_to_blacklist(user_id: int, sender_name: str, template_id: int) -> bool:
    async with PoolConnection() as conn:
        try:
            await conn.execute("INSERT INTO blacklist_senders (user_id, sender_name, template_id) VALUES ($1, $2, $3)", user_id, sender_name, template_id)
            return True
        except Exception as e:
            print(f"Failed to add sender to blacklist. Error: {e}")
            return False


# Получение из бд ключевых слов конкретного пользователя


async def get_user_keywords(user_id):
    async with PoolConnection() as conn:
        if user_id == 'all':
            results = await conn.fetch("SELECT keyword FROM keywords")
        else:
            results = await conn.fetch("SELECT keyword FROM keywords WHERE user_id=$1", user_id)
        return [row['keyword'] for row in results]


async def get_user_blacklistkeywords(user_id):
    async with PoolConnection() as conn:
        if user_id == 'all':
            results = await conn.fetch("SELECT blacklistkeyword FROM blacklistkeywords")
        else:
            results = await conn.fetch("SELECT blacklistkeyword FROM blacklistkeywords WHERE user_id=$1", user_id)
        return [row['blacklistkeyword'] for row in results]

# С шаблона


async def get_keywords_by_template_id(template_id: int):
    async with PoolConnection() as conn:
        results = await conn.fetch("SELECT keyword FROM keywords WHERE template_id = $1", template_id)
        return [row['keyword'] for row in results]


async def get_blacklisted_senders_by_template_id(template_id: int):
    async with PoolConnection() as conn:
        results = await conn.fetch("SELECT sender_name FROM blacklist_senders WHERE template_id = $1", template_id)
        return [row['sender_name'] for row in results]


async def get_stopwords_by_template_id(template_id: int):
    async with PoolConnection() as conn:
        results = await conn.fetch("SELECT blacklistkeyword FROM blacklistkeywords WHERE template_id = $1", template_id)
        return [row['blacklistkeyword'] for row in results]

# Ключевые слова


async def check_keyword_in_db(keyword: str, template_id: int) -> bool:
    async with PoolConnection() as conn:
        result = await conn.fetchrow("SELECT * FROM keywords WHERE keyword = $1 AND template_id = $2", keyword, template_id)
    return bool(result)


async def remove_keyword_from_template(keyword: str, template_id: int) -> bool:
    if not await check_keyword_in_db(keyword, template_id):
        print(f"Keyword '{keyword}' does not exist in the database.")
        return False

    async with PoolConnection() as conn:
        result = await conn.execute("DELETE FROM keywords WHERE keyword = $1 AND template_id = $2", keyword, template_id)
    return result == 'DELETE 1'

# Черные списки


async def add_blacklistkeyword_to_tamplate(user_id: int, blacklistkeyword: str, template_id: int) -> bool:
    async with PoolConnection() as conn:
        try:
            await conn.execute(
                "INSERT INTO blacklistkeywords (user_id, blacklistkeyword, template_id) VALUES ($1, $2, $3)",
                int(user_id), blacklistkeyword, int(template_id)
            )
            return True
        except Exception as e:
            print(e)
            return False


async def check_blacklistkeyword_in_db(blacklistkeyword: str, template_id: int) -> bool:
    async with PoolConnection() as conn:
        result = await conn.fetchrow(
            "SELECT * FROM blacklistkeywords WHERE blacklistkeyword = $1 AND template_id = $2",
            blacklistkeyword, template_id
        )
    return True if result else False


async def remove_blacklistkeyword_from_template(blacklistkeyword: str, template_id: int) -> bool:
    if not await check_blacklistkeyword_in_db(blacklistkeyword, template_id):
        print(
            f"Blacklist keyword '{blacklistkeyword}' does not exist in the database.")
        return False

    async with PoolConnection() as conn:
        try:
            await conn.execute(
                "DELETE FROM blacklistkeywords WHERE blacklistkeyword = $1 AND template_id = $2",
                blacklistkeyword, template_id
            )
            return True
        except Exception as e:
            print(e)
            return False


async def check_sender_in_blacklist(sender_name: str, template_id: str) -> bool:
    async with PoolConnection() as conn:
        result = await conn.fetchrow("SELECT * FROM blacklist_senders WHERE sender_name = $1 AND template_id = $2", sender_name, template_id)
    return bool(result)


async def remove_sender_from_blacklist(sender_name: str, template_id: str) -> bool:
    if not await check_sender_in_blacklist(sender_name, template_id):
        print(
            f"Sender '{sender_name}' is not in the blacklist for template '{template_id}'.")
        return False

    async with PoolConnection() as conn:
        result = await conn.execute("DELETE FROM blacklist_senders WHERE sender_name = $1 AND template_id = $2", sender_name, template_id)
    return result == 'DELETE 1'

# Запросы пользователей


async def add_user(user_id, user_name, user_chat_id):
    async with PoolConnection() as conn:
        await conn.execute("INSERT INTO users (user_id, user_name, user_chat_id) VALUES ($1, $2, $3)", user_id, user_name, user_chat_id)


async def get_users_list():
    async with PoolConnection() as conn:
        return await conn.fetch("SELECT user_id, user_name, user_chat_id FROM users")


async def remove_user(user_id, user_name):
    async with PoolConnection() as conn:
        await conn.execute("DELETE FROM users WHERE user_id=$1 AND user_name=$2", user_id, user_name)

# Группы


async def add_group(group_id, group_name, add_by_userid, link):
    async with PoolConnection() as conn:
        await conn.execute("INSERT INTO groups (group_name, group_id, add_by_userid, link) VALUES ($1, $2, $3, $4)", group_name, group_id, add_by_userid, link)


async def get_user_group_list(user_id):
    async with PoolConnection() as conn:
        return await conn.fetch("SELECT group_id, group_name, add_by_userid FROM groups WHERE add_by_userid = $1", user_id)


async def get_template_group_list(template_id):
    async with PoolConnection() as conn:
        group_list = await conn.fetch(
            "SELECT group_id, group_name, add_by_userid, link FROM groups WHERE template_id = $1", template_id
        )
        return group_list


async def add_group_template(group_id, group_name, add_by_userid, template_id, link):
    async with PoolConnection() as conn:
        await conn.execute(
            "INSERT INTO groups (group_name, group_id, add_by_userid, template_id, link) VALUES ($1, $2, $3, $4, $5)",
            group_name, int(group_id), int(add_by_userid), template_id, link
        )


async def get_all_group_list():
    async with PoolConnection() as conn:
        return await conn.fetch("SELECT group_id, group_name, add_by_userid FROM groups")


async def remove_group(add_by_userid, group_id):
    async with PoolConnection() as conn:
        await conn.execute("DELETE FROM groups WHERE add_by_userid=$1 AND group_id=$2", add_by_userid, group_id)

# Шаблоны


async def get_templates_by_user_id(user_id):
    async with PoolConnection() as conn:
        rows = await conn.fetch("SELECT * FROM templates WHERE user__id=$1", user_id)
    columns = ["id", "template_name", "user__id", "is_select"]
    return [dict(zip(columns, row)) for row in rows]


async def add_template(template_name, user_id):
    try:
        async with PoolConnection() as conn:
            await conn.execute("INSERT INTO templates (template_name, user__id, is_select) VALUES ($1, $2, $3)", template_name, user_id, 0)
            return True
    except Exception as e:
        print(f"Error occurred while adding template: {e}")
        return False


async def delete_template(template_id):
    async with PoolConnection() as conn:
        try:
            await conn.execute("DELETE FROM templates WHERE id = $1", int(template_id))
            return True
        except Exception as e:
            print(f"Error occurred while selecting template: {e}")
            return False


async def remove_groupTemplate(add_by_userid, group_id, template_id):
    async with PoolConnection() as conn:
        try:
            await conn.execute("DELETE FROM groups WHERE add_by_userid=$1 AND group_id=$2 AND template_id=$3", add_by_userid, int(group_id), template_id)
        except Exception as e:
            print(f"Error occurred while selecting template: {e}")


async def select_template(user_id, template_id):
    async with PoolConnection() as conn:
        try:
            await conn.execute("UPDATE templates SET is_select = 0 WHERE user__id = $1", user_id)
            await conn.execute("UPDATE templates SET is_select = 1 WHERE user__id = $1 AND id = $2", user_id, template_id)
            return True
        except Exception as e:
            print(f"Error occurred while selecting template: {e}")
            return False


async def find_selected_template(user_id):
    async with PoolConnection() as conn:
        return await conn.fetchrow("SELECT * FROM templates WHERE user__id = $1 AND is_select = 1", user_id)


async def get_template_name_by_id(id):
    async with PoolConnection() as conn:
        template = await conn.fetchval("SELECT template_name FROM templates WHERE id = $1", id)
    return template if template else None
