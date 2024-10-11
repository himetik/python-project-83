from dotenv import load_dotenv
import psycopg2
import os
from datetime import date
from psycopg2.extras import DictCursor


load_dotenv()


DATABASE_URL = os.getenv('DATABASE_URL')


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def execute_query(query, params=None):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def execute_query_single_row(query, params=None):
    results = execute_query(query, params)
    return results[0] if results else None


def is_url_in_db(url):
    query = "SELECT id FROM urls WHERE name = %s;"
    result = execute_query_single_row(query, (url,))
    return result['id'] if result else None


def add_url(url):
    query = """
    INSERT INTO urls (name, created_at)
    VALUES (%s, %s)
    RETURNING id
    """
    created_at = date.today().isoformat()
    result = execute_query_single_row(query, (url, created_at))
    return result['id']


def find_url(id):
    query = "SELECT * FROM urls WHERE id = %s"
    result = execute_query_single_row(query, (id,))
    return dict(result) if result else None


def list_urls():
    query = "SELECT * FROM urls ORDER BY id DESC;"
    return [dict(row) for row in execute_query(query)]


if __name__ == "__main__":
    print(list_urls())