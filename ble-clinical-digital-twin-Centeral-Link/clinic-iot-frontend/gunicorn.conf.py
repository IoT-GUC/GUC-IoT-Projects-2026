import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("SERVER_HOST", "127.0.0.1")
port = os.getenv("SERVER_PORT", "8050")

bind = f"{host}:{port}"
workers = 2