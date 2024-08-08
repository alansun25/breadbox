from datetime import datetime
from notion_client import Client
from groq import Groq
from typing import Optional, TypedDict
import os


class Transaction(TypedDict):
    merchant: str
    spend: float
    date: str
    category: Optional[str]


class NotionClient:

    def __init__(self):
        self.client = Client(auth=os.environ.get("NOTION_TOKEN"))
        self.db_id = os.environ.get("TEST_DATABASE_ID")
        # TODO: Change to actual DB when ready

    def get_categories(self):
        response = self.client.databases.retrieve(database_id=self.db_id)
        options = response["properties"]["category"]["select"]["options"]
        categories = {
            option["name"][2:].replace(" ", ""): option["name"]
            for option in options
        }
        return categories

    def get_iso_date(self, date: str):
        return datetime.strptime(date, "%m/%d/%Y").isoformat()[:10]

    def get_transaction_object(self, transaction: Transaction):
        return {
            "merchant": {
                "title": [{"text": {"content": transaction["merchant"]}}]
            },
            "category": {"select": {"name": transaction["category"]}},
            "spend": {"number": transaction["spend"]},
            "date": {"date": {"start": self.get_iso_date(transaction["date"])}},
        }

    def add_transactions(self, transactions: list[Transaction]):
        for transaction in transactions:
            props = self.get_transaction_object(transaction)
            self.client.pages.create(
                parent={"database_id": self.db_id}, properties=props
            )


class GroqClient:

    def __init__(
        self,
        transactions: list[Transaction],
        categories: dict[str, str],
    ):
        self.client = Groq(api_key=os.environ.get("GROQ_TOKEN"))
        self.transactions = transactions
        self.categories = categories

    def format_transaction(self, index: int, transaction: Transaction):
        if transaction.category is not None:
            template = "{index}. Merchant: {merchant}, Price: {spend}, Category: {category}"
            return template.format(
                index=index,
                merchant=transaction["merchant"],
                category=transaction["category"],
                spend=transaction["spend"],
            )
        else:
            template = "{index}. Merchant: {merchant}, Price: {spend}"
            return template.format(
                index=index,
                merchant=transaction["merchant"],
                spend=transaction["spend"],
            )

    def generate_prompt(self):
        with open(f"./prompt.txt", "r") as prompt:
            formatted_transactions = [
                self.format_transaction(i + 1, transaction)
                for i, transaction in enumerate(self.transactions)
            ]
            transactions_str = "\n".join(formatted_transactions)
            categories_str = "\n".join(self.categories.keys())

            formatted_prompt = prompt.read().format(
                categories=categories_str, transactions=transactions_str
            )

            return formatted_prompt

    def llm_categorization(self, prompt: str):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a budgeting assistant.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            model="llama3-70b-8192",
        )

        return chat_completion.choices[0].message.content

    def valid_response(
        self,
        response: str | None,
    ):
        if response is None:
            return False

        llm_categories = response.split(", ")
        proper_num = len(llm_categories) == len(self.transactions)
        proper_content = all(
            category in self.categories.keys() for category in llm_categories
        )

        return all([proper_num, proper_content])

    def attach_categories(
        self,
        generated_categories: str,
    ):
        categories = generated_categories.split(", ")

    def categorize_transactions(self):
        prompt = self.generate_prompt()  # TODO: Move to init
        response = self.llm_categorization(prompt)

        if not self.valid_response(response):
            return self.categorize_transactions()

        # TODO

        return self.transactions
