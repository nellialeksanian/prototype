from dotenv import load_dotenv
import os
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GIGACHAT_TOKEN = os.getenv("GIGACHAT_TOKEN")
GIGACHAT_TOKEN_MAX = os.getenv("GIGACHAT_TOKEN_MAX")
DATABASE_URL = os.getenv("DATABASE_URL")
GRAPH_FILE = os.getenv('GRAPH_FILE')
EXHIBITION_DESCRIPTION = os.getenv('EXHIBITION_DESCRIPTION')