import psycopg2
from psycopg2 import pool
from typing import Callable, Optional, List, Tuple
from dataclasses import dataclass
from datetime import date
import logging
from functools import wraps

from page_analyzer.config import DATABASE_URL, MINCONN, MAXCONN


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


@dataclass
class Check:
    url_id: Optional[int] = None
    status_code: Optional[int] = None
    h1: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[date] = None
    id: Optional[int] = None


@dataclass
class Url:
    name: str
    id: int
    created_at: Optional[date] = None


class DatabasePool:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pool = pool.SimpleConnectionPool(
                minconn=MINCONN, maxconn=MAXCONN, dsn=DATABASE_URL
            )
        return cls._instance

    def get_connection(self):
        return self.pool.getconn()

    def return_connection(self, conn):
        self.pool.putconn(conn)


def db_connection(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, conn: Optional[psycopg2.extensions.connection] = None, **kwargs):
        db_pool = DatabasePool()
        if conn is None:
            conn = db_pool.get_connection()
        try:
            result = func(conn=conn, *args, **kwargs)
            conn.commit()
            return result
        except psycopg2.DatabaseError as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            db_pool.return_connection(conn)
    return wrapper


@db_connection
def get_url_id(*, conn: psycopg2.extensions.connection, url_name: str) -> Optional[int]:
    query = "SELECT id FROM urls WHERE name = %s;"
    with conn.cursor() as cursor:
        cursor.execute(query, (url_name,))
        row = cursor.fetchone()
    return row[0] if row else None


@db_connection
def get_url_checks(*, conn: psycopg2.extensions.connection, url_id: int) -> List[Check]:
    query = """
        SELECT id, status_code, COALESCE(h1, ''), COALESCE(title, ''),
               COALESCE(description, ''), created_at
        FROM url_checks
        WHERE url_id = %s"""
    with conn.cursor() as cursor:
        cursor.execute(query, (url_id,))
        raw_checks = cursor.fetchall()
    return [Check(id=id, status_code=status_code, h1=h1, title=title,
                  description=description, created_at=created_at)
            for id, status_code, h1, title, description, created_at in raw_checks]


@db_connection
def get_url(*, conn: psycopg2.extensions.connection, url_id: int) -> Optional[Url]:
    query = "SELECT id, name, created_at FROM urls WHERE id = %s"
    with conn.cursor() as cursor:
        cursor.execute(query, (url_id,))
        url_row = cursor.fetchone()
    return Url(id=url_row[0], name=url_row[1], created_at=url_row[2]) if url_row else None


@db_connection
def get_all_urls_with_last_check(
    *, conn: psycopg2.extensions.connection
) -> List[Tuple[Url, Check]]:
    query = """
        SELECT DISTINCT ON (u.id)
            u.id, u.name, MAX(uc.created_at) AS last_check, uc.status_code
        FROM urls u
        LEFT JOIN url_checks uc ON u.id = uc.url_id
        GROUP BY u.id, u.name, uc.status_code
        ORDER BY u.id DESC
    """
    with conn.cursor() as cursor:
        cursor.execute(query)
        raw_urls = cursor.fetchall()
    return [(Url(id=id, name=name),
             Check(created_at=last_check, status_code=status_code))
            for id, name, last_check, status_code in raw_urls]


@db_connection
def add_url(*, conn: psycopg2.extensions.connection, url_name: str) -> int:
    query = "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id"
    with conn.cursor() as cursor:
        cursor.execute(query, (url_name, date.today()))
        url_id = cursor.fetchone()[0]
    return url_id


@db_connection
def add_check(*, conn: psycopg2.extensions.connection, check: Check) -> None:
    query = """
        INSERT INTO url_checks
        (url_id, status_code, h1, title, description, created_at)
        VALUES (%(url_id)s, %(status_code)s, %(h1)s, %(title)s, %(description)s, %(created_at)s)
    """
    with conn.cursor() as cursor:
        cursor.execute(query, {**check.__dict__, 'created_at': date.today()})
