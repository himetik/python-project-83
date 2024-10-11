import psycopg2
from psycopg2 import pool
from typing import Callable, Any, List, Tuple
from page_analyzer.config import DATABASE_URL, MINCONN, MAXCONN
from dataclasses import dataclass
from datetime import date


@dataclass
class Check:
    url_id: int | None = None
    status_code: int | None = None
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
    def wrapper(**kwargs):
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
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM urls WHERE name = %s;", (url_name,))
        url_id_row = cursor.fetchone()
        return url_id_row[0] if url_id_row else None


@make_db_connection
def get_url_checks(*, conn: Any, url_id: int) -> List[Check]:
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, status_code, created_at
            FROM url_checks
            WHERE url_id = %s
        """, (url_id,))
        return [Check(id=id, status_code=status_code, created_at=created_at)
                for id, status_code, created_at in cursor.fetchall()]


@make_db_connection
def get_url(*, conn: Any, url_id: int) -> Url | None:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
        url_row = cursor.fetchone()
        return Url(id=url_row[0], name=url_row[1], created_at=url_row[2]) if url_row else None


@make_db_connection
def get_all_urls_with_last_check(*, conn: Any) -> List[Tuple[Url, Check]]:
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT ON (urls.id)
                urls.id, urls.name, MAX(url_checks.created_at) AS last_check,
                url_checks.status_code
            FROM urls
            LEFT JOIN url_checks ON urls.id = url_checks.url_id
            GROUP BY urls.id, urls.name, url_checks.status_code
            ORDER BY urls.id DESC
        """)
        return [(Url(id=id, name=name), Check(created_at=last_check, status_code=status_code))
                for id, name, last_check, status_code in cursor.fetchall()]


@make_db_connection
def add_url(*, conn: Any, url_name: str) -> int:
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO urls (name, created_at)
            VALUES (%s, %s)
            RETURNING id
        """, (url_name, date.today()))
        return cursor.fetchone()[0]


@make_db_connection
def add_check(*, conn: Any, check: Check) -> None:
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO url_checks (url_id, status_code, created_at)
            VALUES (%(url_id)s, %(status_code)s, %(created_at)s)
        """, {
            "url_id": check.url_id,
            "status_code": check.status_code,
            "created_at": date.today(),
        })
