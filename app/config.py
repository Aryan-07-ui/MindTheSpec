import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "mindthespec-dev-insecure-secret-key-391823719827391")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "mindthespec_session")
APP_ENV = os.getenv("APP_ENV", "development")
ALGORITHM = "HS256"
SESSION_EXPIRE_HOURS = 24
