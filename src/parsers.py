import pandas as pd


def parse_chase_transactions(file: str):
    chase = pd.read_csv(file)
    pass


def parse_mastercard_transactions(file: str):
    mastercard = pd.read_csv(
        file,
        sep=",",
        names=["date", "amount", "ignore1", "ignore2", "merchant"],
    )
    pass


def parse_schwab_transactions(file: str):
    schwab = pd.read_csv(file)
    pass


def parse_venmo_transactions(file: str):
    venmo = pd.read_csv(file)
    pass


def parse_transactions(file: str, bank: str):
    if bank == "chase":
        return parse_chase_transactions(file)
    elif bank == "mastercard":
        return parse_mastercard_transactions(file)
    elif bank == "schwab":
        return parse_schwab_transactions(file)
    elif bank == "venmo":
        return parse_venmo_transactions(file)
