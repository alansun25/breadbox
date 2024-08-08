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

    def strip_whitespace(self, string: str):
        if string.startswith(" ") or string.endswith(" "):
            return self.strip_whitespace(string.strip())

        return string

    def get_categories(self):
        response = self.client.databases.retrieve(database_id=self.db_id)
        options = response["properties"]["category"]["select"]["options"]
        categories = {
            self.strip_whitespace(option["name"][2:]): option["name"]
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

    def __init__(self, categories: dict[str, str]):
        self.client = Groq(api_key=os.environ.get("GROQ_TOKEN"))
        self.categories = categories
        self.tries = 0
        self.system_message = self.get_system_message()

    def get_system_message(self):
        with open(os.path.abspath("src/input/system.txt"), "r") as system:
            return system.read()

    def format_transaction(self, index: int, transaction: Transaction):
        if transaction["category"] is not None:
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

    def generate_prompt(self, transactions: list[Transaction]):
        with open(os.path.abspath("src/input/prompt.txt"), "r") as prompt:
            formatted_transactions = [
                self.format_transaction(i + 1, transaction)
                for i, transaction in enumerate(transactions)
            ]
            transactions_str = "\n".join(formatted_transactions)
            categories_str = "\n".join(self.categories.keys())

            formatted_prompt = prompt.read().format(
                categories=categories_str, transactions=transactions_str
            )

            return formatted_prompt

    def get_categories(self, prompt):
        # TODO: The LLM has trouble handling a lot of transactions at once.
        # Break this into a multi-turn conversation that processes 10
        # transactions at a time. Need to modify prompt.

        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": self.system_message,
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
        transactions: list[Transaction],
    ):
        if response is None:
            print("No response received.")
            return False

        llm_categories = [category.strip() for category in response.split(",")]

        num_categories = len(llm_categories)
        num_transactions = len(transactions)
        if not num_categories == num_transactions:
            print(
                f"Invalid response string. Num categories: {num_categories}, Num transactions: {num_transactions}"
            )
            return False

        if not all(
            category in self.categories.keys() for category in llm_categories
        ):
            print(f"Invalid categories received in response.")
            return False

    def attach_categories(
        self,
        generated_categories: str,
    ):
        categories = generated_categories.split(", ")

    def categorize_transactions(self, transactions: list[Transaction]):
        self.tries += 1
        prompt = self.generate_prompt(transactions)
        response = self.get_categories(prompt)

        if not self.valid_response(response, transactions):
            print(f"Try {self.tries} failed. Response: {response}")
            return self.categorize_transactions(transactions)

        return response  # TODO: For testing the response

        # TODO: attach_categories
        # then
        # return self.transactions
