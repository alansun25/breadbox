import datetime as dt
from notion_client import Client
from groq import Groq
from typing import Optional, TypedDict
import os


class Transaction(TypedDict):
    merchant: str
    spend: float
    date: str
    method: str
    category: Optional[str]


class NotionClient:

    def __init__(self):
        self.client = Client(auth=os.environ.get("NOTION_TOKEN"))
        self.transactions_db_id = os.environ.get("TRANSACTIONS_DATABASE_ID")
        self.summary_db_id = os.environ.get("SUMMARY_DATABASE_ID")
        self.prev_month_summary_page_id = self.get_prev_month_summary_page_id()

    def strip_whitespace(self, string: str):
        if string.startswith(" ") or string.endswith(" "):
            return self.strip_whitespace(string.strip())

        return string

    def get_prev_month_and_year(self):
        current_date = dt.date.today()
        previous_month = current_date.replace(day=1) - dt.timedelta(days=1)
        previous_month_name = previous_month.strftime("%B")[:3]
        current_year = current_date.strftime("%Y")
        if previous_month_name == "Dec":
            current_year = str(current_date.year - 1)

        return f"{previous_month_name} {current_year}"

    def get_prev_month_summary_page_id(self):
        month_and_year = self.get_prev_month_and_year()
        page_details = self.client.databases.query(
            **{
                "database_id": self.summary_db_id,
                "filter": {
                    "property": "name",
                    "rich_text": {
                        "contains": month_and_year.lower(),
                    },
                },
            }
        )
        page_id = page_details["results"][0]["id"]

        return page_id

    def add_paychecks(self, paychecks_values: list[float]):
        page_id = self.prev_month_summary_page_id
        paychecks_object = {
            f"paycheck {i + 1}": {"number": paycheck}
            for i, paycheck in enumerate(paychecks_values)
        }
        self.client.pages.update(
            **{
                "page_id": page_id,
                "properties": paychecks_object,
            }
        )

    def add_venmo_repay(self, repay_value: float):
        page_id = self.prev_month_summary_page_id
        self.client.pages.update(
            **{
                "page_id": page_id,
                "properties": {"venmo repay": {"number": repay_value}},
            }
        )

    def get_categories(self):
        response = self.client.databases.retrieve(
            database_id=self.transactions_db_id
        )
        options = response["properties"]["category"]["select"]["options"]
        categories = {
            self.strip_whitespace(option["name"][2:]): option["name"]
            for option in options
        }
        return categories

    def get_transaction_object(self, transaction: Transaction):
        return {
            "merchant": {
                "title": [{"text": {"content": transaction["merchant"]}}]
            },
            "category": {"select": {"name": transaction["category"]}},
            "spend": {"number": transaction["spend"]},
            "method": {"select": {"name": transaction["method"]}},
            "date": {"date": {"start": transaction["date"]}},
        }

    def add_transactions(self, transactions: list[Transaction]):
        for transaction in transactions:
            props = self.get_transaction_object(transaction)
            self.client.pages.create(
                parent={"database_id": self.transactions_db_id},
                properties=props,
            )


class GroqClient:

    def __init__(self, categories: dict[str, str]):
        self.client = Groq(api_key=os.environ.get("GROQ_TOKEN"))
        self.categories = categories
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
            return False, "No response received."

        llm_categories = [category.strip() for category in response.split(",")]

        num_categories = len(llm_categories)
        num_transactions = len(transactions)
        if not num_categories == num_transactions:
            return (
                False,
                f"Invalid response string. Num categories: {num_categories}, Num transactions: {num_transactions}",
            )

        if not all(
            category in self.categories.keys() for category in llm_categories
        ):
            return False, f"Invalid categories received in response."

        return True, None

    def attach_categories(
        self,
        response: str,
        transactions: list[Transaction],
    ):
        categories = [
            self.categories[category.strip()]
            for category in response.split(",")
        ]
        for i, transaction in enumerate(transactions):
            transaction["category"] = categories[i]

        return transactions

    def categorize_transactions(self, transactions: list[Transaction]):
        for i in range(0, len(transactions), 10):
            subset = transactions[i : i + 10]
            prompt = self.generate_prompt(subset)
            response = self.get_categories(prompt)

            retries = 5
            valid = self.valid_response(response, subset)
            while not valid[0] and retries > 0:
                print(
                    f"Response validation failed.\nError: {valid[1]}\nResponse: {response}"
                )
                response = self.get_categories(prompt)
                valid = self.valid_response(response, subset)
                retries -= 1

            if not valid[0]:
                raise Exception("Failed to validate response after 5 attempts.")

            transactions[i : i + 10] = self.attach_categories(response, subset)

        return transactions
