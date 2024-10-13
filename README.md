# Page Analyzer - Web Application for URL Analysis

[![Actions Status](https://github.com/himetik/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/himetik/python-project-83/actions)
[![Maintainability](https://api.codeclimate.com/v1/badges/5ab0eed3f882dc4efc3b/maintainability)](https://codeclimate.com/github/himetik/python-project-83/maintainability)

## Description
This web application helps users analyze web pages by extracting key elements such as the page title, meta description, and other SEO-related information.

## Tech Stack

### Backend Technologies
- Flask
- PostgreSQL
- Gunicorn

### Parsing
- BeautifulSoup4

### Tools & Dependencies
- Python 3.7+
- Poetry
- Git
- Make

### Requirements
- Python 3.7+
- pip
- PostgreSQL 12+
- poetry
- git
- make

### Installation
Before launching the project locally, ensure that PostgreSQL is installed and a database is created. Set up the `urls` and `url_checks` tables within this database according to the structure defined in `database.sql`. Additionally, create a `.env` file with the necessary settings, using `example.env` as a reference. Both configuration files can be found in the project's root directory.

```sh
git clone git@github.com:himetik/python-project-83.git
cd python-project-83
poetry shell
poetry install
make start
```

### Deployment
To deploy the application to a server, you can use services like Render, Heroku, or a dedicated VPS. Ensure PostgreSQL and Gunicorn are properly configured.

### Web site
https://python-project-83-ll03.onrender.com
