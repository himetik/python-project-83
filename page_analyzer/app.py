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


app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.post("/urls")
def add_url() -> str | tuple[str, int] | Response:
    raw_url = request.form.get("url")
    url = normalize_url(raw_url)

    if not validate_url(url):
        return handle_flash_and_render("Некорректный URL", "danger", "index.html", HTTPStatus.UNPROCESSABLE_ENTITY)

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
        return render_template("show_url.html", url=url, checks=sorted_checks, messages=messages)

    return render_template("404.html"), HTTPStatus.NOT_FOUND


@app.get("/urls")
def show_urls() -> str:
    urls_data = db.get_all_urls_with_last_check()
    return render_template("list_urls.html", urls_data=urls_data)


@app.post("/urls/<int:id>/checks")
def initialize_check(id: int) -> Response:
    url = db.get_url(url_id=id)

    if not url:
        return handle_flash_and_redirect("Произошла ошибка при проверке", "danger", "show_url_info", id)

    try:
        response = requests.get(url.name)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return handle_flash_and_redirect("Произошла ошибка при проверке", "danger", "show_url_info", id)

    accessibility_data = {}  
    check = Check(url_id=id, **accessibility_data)
    db.add_check(check=check)
    flash("Страница успешно проверена", "success")

    return redirect(url_for("show_url_info", id=id))


def normalize_url(url: str) -> str:
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def validate_url(url: str) -> bool:
    return validator(url)


def handle_flash_and_render(message: str, category: str, template: str, status_code: int) -> tuple[str, int]:
    flash(message, category)
    messages = get_flashed_messages(with_categories=True)
    return render_template(template, messages=messages), status_code


def handle_flash_and_redirect(message: str, category: str, endpoint: str, id: int) -> Response:
    flash(message, category)
    return redirect(url_for(endpoint, id=id))
