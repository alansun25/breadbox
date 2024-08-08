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

    def __init__(self):
        self.client = Groq(api_key=os.environ.get("GROQ_TOKEN"))

    # TODO: Account for lack of categories in the prompt instructions;
    # this will allow me to standardize into one prompt
    def format_transaction(self, index: int, transaction: Transaction):
        template = "{index}. Merchant: {merchant}, Category: {category}, Price: {spend}"
        return template.format(
            index=index,
            merchant=transaction["merchant"],
            category=transaction["category"],
            spend=transaction["spend"],
        )

    def categorize(
        self, bank, transactions: list[Transaction], categories: dict[str, str]
    ):
        # TODO
        with open(f"../prompts/{bank}_prompt.txt", "r") as prompt:
            formatted_transactions = [
                self.format_transaction(i + 1, transaction)
                for i, transaction in enumerate(transactions)
            ]
            transactions_str = "\n".join(formatted_transactions)
            categories_str = "\n".join(categories.keys())

            formatted_prompt = prompt.read().format(
                categories=categories_str, transactions=transactions_str
            )

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a budgeting assistant.",
                    },
                    {
                        "role": "user",
                        "content": formatted_prompt,
                    },
                ],
                model="llama3-70b-8192",
            )

    # def test(self):
    #     chat_completion = self.client.chat.completions.create(
    #         messages=[
    #             {"role": "system", "content": "You are a friendly assistant."},
    #             {
    #                 "role": "user",
    #                 "content": "Hi there! Please respond with a poem about the ocean.",
    #             },
    #         ],
    #         model="llama3-70b-8192",
    #     )
    #     return chat_completion.choices[0].message.content
