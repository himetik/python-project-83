import psycopg2
from psycopg2 import pool
from typing import Callable, Any
from page_analyzer.config import DATABASE_URL, MINCONN, MAXCONN
from dataclasses import dataclass
from datetime import date


@dataclass
class Check:
    url_id: int | None = None
    created_at: date | None = None
    id: int | None = None


@dataclass
class Url:
    name: str
    id: int
    created_at: date | None = None


Pool = pool.SimpleConnectionPool(
    minconn=MINCONN, maxconn=MAXCONN, dsn=DATABASE_URL
)


def make_db_connection(query_func: Callable) -> Callable:
    def wrapper(*, conn=None, **kwargs):
        if not conn:
            conn = Pool.getconn()
        try:
            result = query_func(conn=conn, **kwargs)
            conn.commit()
            return result
        except psycopg2.DatabaseError:
            conn.rollback()
        finally:
            Pool.putconn(conn)

    return wrapper


@make_db_connection
def get_url_id(*, conn: Any, url_name: str) -> int | None:
    query = """
        SELECT id
        FROM urls
        WHERE name = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(query, (url_name,))
        url_id_row = cursor.fetchone()
    return url_id_row[0] if url_id_row else None


@make_db_connection
def get_url_checks(*, conn: Any, url_id: int) -> list[Check]:
    query = """
        SELECT id, created_at
        FROM url_checks
        WHERE url_id = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(query, (url_id,))
        raw_checks = cursor.fetchall()
    return [Check(id=id, created_at=created_at) for id, created_at in raw_checks]


@make_db_connection
def get_url(*, conn: Any, url_id: int) -> Url | None:
    query = """
        SELECT id, name, created_at
        FROM urls
        WHERE id = %s;
    """
    with conn.cursor() as cursor:
        cursor.execute(query, (url_id,))
        url_row = cursor.fetchone()
    if url_row:
        url_id, name, created_at = url_row
        return Url(id=url_id, name=name, created_at=created_at)
    return None


@make_db_connection
def get_all_urls_with_last_check(*, conn: Any) -> list[tuple[Url, Check]]:
    query = """
        SELECT DISTINCT ON (urls.id)
            urls.id,
            urls.name,
            MAX(url_checks.created_at) AS last_check
        FROM urls
        LEFT JOIN url_checks ON urls.id = url_checks.url_id
        GROUP BY urls.id, urls.name
        ORDER BY urls.id DESC;
    """
    with conn.cursor() as cursor:
        cursor.execute(query)
        raw_urls = cursor.fetchall()
    return [
        (Url(id=id, name=name), Check(created_at=last_check))
        for id, name, last_check in raw_urls
    ]


@make_db_connection
def add_url(*, conn: Any, url_name: str) -> int:
    created_at = date.today()
    query = """
        INSERT INTO urls (name, created_at)
        VALUES (%s, %s)
        RETURNING id;
    """
    with conn.cursor() as cursor:
        cursor.execute(query, (url_name, created_at))
        return cursor.fetchone()[0]


@make_db_connection
def add_check(*, conn: Any, check: Check) -> None:
    created_at = date.today()
    query = """
        INSERT INTO url_checks (url_id, created_at)
        VALUES (%(url_id)s, %(created_at)s);
    """
    with conn.cursor() as cursor:
        cursor.execute(
            query,
            {
                "url_id": check.url_id,
                "created_at": created_at,
            },
        )
