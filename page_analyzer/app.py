from flask import (
    Flask,
    render_template,
    request,
    flash,
    get_flashed_messages,
    url_for,
    redirect,
)
import requests
from requests import Response
from validators import url as validator
from http import HTTPStatus
import page_analyzer.db as db
from .config import SECRET_KEY
from .db import Check
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Union, Tuple

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.post("/urls")
def add_url() -> Union[str, Tuple[str, int], Response]:
    url = normalize_url(request.form.get("url"))
    if not validator(url):
        flash("Некорректный URL", "danger")
        return render_template(
            "index.html",
            messages=get_flashed_messages(with_categories=True)
        ), HTTPStatus.UNPROCESSABLE_ENTITY

    url_id = db.get_url_id(url_name=url)
    if url_id:
        flash("Страница уже существует", "info")
    else:
        url_id = db.add_url(url_name=url)
        flash("Страница успешно добавлена", "success")
    
    return redirect(url_for("show_url_info", id=url_id))


@app.route("/urls/<int:id>")
def show_url_info(id: int) -> Union[str, Tuple[str, int]]:
    url = db.get_url(url_id=id)
    if not url:
        return render_template("404.html"), HTTPStatus.NOT_FOUND

    checks = sorted(db.get_url_checks(url_id=id), key=lambda x: x.id, reverse=True)
    messages = get_flashed_messages(with_categories=True)
    return render_template("show_url.html", url=url, checks=checks, messages=messages)


@app.get("/urls")
def show_urls() -> str:
    urls_data = db.get_all_urls_with_last_check()
    return render_template("list_urls.html", urls_data=urls_data)


@app.post("/urls/<int:id>/checks")
def initialize_check(id: int) -> Response:
    url = db.get_url(url_id=id)
    try:
        response = requests.get(url.name, timeout=10)
        response.raise_for_status()
        accessibility_data = get_accessibility_content(response)
        check = Check(url_id=id, **accessibility_data)
        db.add_check(check=check)
        flash("Страница успешно проверена", "success")
    except requests.exceptions.RequestException:
        flash("Произошла ошибка при проверке", "danger")
    except Exception as e:
        flash(f"Ошибка при анализе доступности: {str(e)}", "danger")

    return redirect(url_for("show_url_info", id=id))


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def get_accessibility_content(response: Response) -> dict:
    return {"status_code": response.status_code}
