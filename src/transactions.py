from clients import NotionClient, GroqClient
from parsers import (
    parse_chase_transactions,
    parse_mastercard_transactions,
    parse_schwab_transactions,
    parse_venmo_transactions,
)


def get_file_string(directory, provider):
    return f"{directory}/{provider}.csv"


def get_parsed_transactions(transactions_folder):
    directory = f"./transactions/{transactions_folder}"
    return (
        parse_chase_transactions(get_file_string(directory, "chase")),
        parse_mastercard_transactions(get_file_string(directory, "mastercard")),
        parse_schwab_transactions(get_file_string(directory, "schwab")),
        parse_venmo_transactions(get_file_string(directory, "venmo")),
    )


def update_transactions_table(transactions_folder):
    notion = NotionClient()
    groq = GroqClient()

    parsed_transactions = get_parsed_transactions(transactions_folder)
    for p in parsed_transactions:
        pass
    pass
