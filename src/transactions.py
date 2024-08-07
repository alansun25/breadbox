from clients import NotionClient, GroqClient
from parsers import parse_transactions

BANKS = ["chase", "mastercard", "schwab", "venmo"]


def get_file_string(directory, provider):
    return f"{directory}/{provider}.csv"


def get_parsed_transactions(transactions_folder):
    directory = f"./transactions/{transactions_folder}"
    return {
        bank: parse_transactions(get_file_string(directory, bank))
        for bank in BANKS
    }


def update_transactions_table(transactions_folder):
    notion = NotionClient()
    groq = GroqClient()

    parsed_transactions = get_parsed_transactions(transactions_folder)
    for bank, transactions in parsed_transactions.items():
        groq.categorize(bank, transactions)  # TODO: In place?

        # TODO: One at a time or all at once?
        # for transaction in transactions:
        #     notion.add_transaction(transaction)
