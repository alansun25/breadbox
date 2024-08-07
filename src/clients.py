from dotenv import load_dotenv
from notion_client import Client
from groq import Groq
import os


class NotionClient:
    def __init__(self):
        self.client = Client(auth=os.environ.get("NOTION_TOKEN"))
        self.db_id = os.environ.get("FINANCE_DATABASE_ID")

    def add_transaction(self, transaction):
        # TODO
        pass


class GroqClient:
    def __init__(self):
        self.client = Groq(api_key=os.environ.get("GROQ_TOKEN"))

    def categorize(self, transactions):
        # TODO
        pass
