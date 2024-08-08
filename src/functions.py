from src.classes import NotionClient, GroqClient, Transaction
from src.constants import BANKS, COLNAMES
import os
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


def get_filepath(folder_path: str, bank: str):
    return f"{folder_path}/{bank}.csv"


def get_parsed_transactions(folder_path: str):
    return {
        bank: parse_transactions(get_filepath(folder_path, bank), bank)
        for bank in BANKS
        if os.path.exists(get_filepath(folder_path, bank))
    }


def update_transactions_table(folder_path: str):
    notion = NotionClient()
    categories = notion.get_categories()
    groq = GroqClient(categories)

    parsed_transactions = get_parsed_transactions(folder_path)
    for bank, transactions in parsed_transactions.items():
        transactions = groq.categorize_transactions(transactions)
        print(transactions)
        # notion.add_transactions(transactions)
