from dotenv import load_dotenv
import os


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
MINCONN = os.getenv("MINCONN", "2")
MAXCONN = os.getenv("MAXCONN", "3")
