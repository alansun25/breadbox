from src.classes import NotionClient, GroqClient, Transaction
from src.constants import BANKS, COLNAMES
import pandas as pd


def row_to_dict(row: pd.Series):
    dict_row = Transaction(merchant=None, spend=None, date=None, category=None)
    for key in dict_row.keys():
        if key in row:
            dict_row[key] = row[key]

    return dict_row


# TODO: Might need to refactor this when I see venmo and schwab csv formats
def parse_transactions(file: str, bank: str):
    col_names = COLNAMES[bank]
    transactions = (
        pd.read_csv(
            file,
            sep=",",
            names=col_names,
        )
        .apply(lambda row: row_to_dict(row), axis=1)
        .tolist()
    )

    return transactions


def get_file_string(directory, bank):
    return f"{directory}/{bank}.csv"


def get_parsed_transactions(transactions_folder):
    directory = f"../transactions/{transactions_folder}"
    return {
        bank: parse_transactions(get_file_string(directory, bank))
        for bank in BANKS
    }


def update_transactions_table(transactions_folder):
    notion = NotionClient()
    groq = GroqClient()

    categories = notion.get_categories()

    parsed_transactions = get_parsed_transactions(transactions_folder)
    for bank, transactions in parsed_transactions.items():
        # TODO: In place?
        transactions = groq.categorize_transactions(
            bank, transactions, categories
        )
        notion.add_transactions(transactions)
