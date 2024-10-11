import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, get_flashed_messages, url_for, redirect
import validators
import psycopg2

import page_analyzer.db as db


app = Flask(__name__)
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


def normalize(url):
    o = urlparse(url)
    return f'{o.scheme}://{o.netloc}'


@app.route('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def add_url():
    raw_url = request.form.get('url')
    url = normalize(raw_url)

    if not validators.url(url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html', messages=get_flashed_messages(with_categories=True)), 422

    id = db.is_url_in_db(url)
    if id:
        flash('Страница уже существует', 'info')
        return redirect(url_for('show_url', id=id))
    else:
        url_id = db.add_url(url)
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('show_url', id=url_id))


@app.route('/urls/<int:id>')
def show_url(id):
    url = db.find_url(id)
    messages = get_flashed_messages(with_categories=True)
    return render_template('show_url.html', url=url, messages=messages)


@app.get('/urls')
def show_urls():
    urls = db.list_urls()
    return render_template('list_urls.html', urls=urls)


if __name__ == '__main__':
    app.run(debug=True)
