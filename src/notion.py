from dotenv import load_dotenv
from notion_client import Client
import os


class Notion:
    def __init__(self):
        load_dotenv()
        self.notion = Client(auth=os.environ.get("NOTION_TOKEN"))
        self.db_id = os.environ.get("FINANCE_DATABASE_ID")

    def add_transaction(self):
        # TODO
        pass
