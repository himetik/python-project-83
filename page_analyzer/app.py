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
import logging

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.post("/urls")
def add_url() -> str | tuple[str, int] | Response:
    raw_url = request.form.get("url", "").strip()
    url = normalize_url(raw_url)

    if not validator(url):
        flash("Некорректный URL", "danger")
        messages = get_flashed_messages(with_categories=True)
        return (
            render_template("index.html", messages=messages),
            HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    url_id = db.get_url_id(url_name=url)
    if url_id:
        flash("Страница уже существует", "info")
        return redirect(url_for("show_url_info", id=url_id))

    url_id = db.add_url(url_name=url)
    flash("Страница успешно добавлена", "success")
    return redirect(url_for("show_url_info", id=url_id))


@app.route("/urls/<int:id>")
def show_url_info(id: int) -> str | tuple[str, int]:
    url = db.get_url(url_id=id)
    if url:
        checks = db.get_url_checks(url_id=id)
        sorted_checks = sorted(checks, key=lambda x: x.id, reverse=True)
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            "show_url.html", url=url, checks=sorted_checks, messages=messages
        )
    return render_template("404.html"), HTTPStatus.NOT_FOUND


@app.get("/urls")
def show_urls() -> str:
    urls_data = db.get_all_urls_with_last_check()
    return render_template("list_urls.html", urls_data=urls_data)


@app.post("/urls/<int:id>/checks")
def initialize_check(id: int) -> Response:
    url = db.get_url(url_id=id)

    try:
        response = requests.get(url.name)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к {url.name}: {e}")
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("show_url_info", id=id))

    accessibility_data = get_accessibility_content(response)

    check = Check(url_id=id, **accessibility_data)

    db.add_check(check=check)

    flash("Страница успешно проверена", "success")

    return redirect(url_for("show_url_info", id=id))


def normalize_url(url: str) -> str:
    o = urlparse(url)
    return f"{o.scheme}://{o.netloc}"


def get_accessibility_content(response: Response) -> dict:
    soup = BeautifulSoup(response.text, "html.parser")

    h1_tag = soup.find("h1")
    title_tag = soup.title
    description_tag = soup.find("meta", attrs={"name": "description"})

    return {
        "status_code": response.status_code,
        "h1": h1_tag.text if h1_tag else "",
        "title": title_tag.text if title_tag else "",
        "description": description_tag["content"] if description_tag else "",
    }


@app.errorhandler(404)
def not_found_404(e):
    return render_template("404.html"), HTTPStatus.NOT_FOUND


@app.errorhandler(500)
def internal_error_500(e):
    return render_template("500.html"), HTTPStatus.INTERNAL_SERVER_ERROR
