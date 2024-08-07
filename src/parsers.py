import pandas as pd


def parse_chase_transactions(file):
    chase = pd.read_csv(file)
    pass


def parse_mastercard_transactions(file):
    mastercard = pd.read_csv(file)
    pass


def parse_schwab_transactions(file):
    schwab = pd.read_csv(file)
    pass


def parse_venmo_transactions(file):
    venmo = pd.read_csv(file)
    pass


def parse_transactions(file, bank):
    if bank == "chase":
        return parse_chase_transactions(file)
    elif bank == "mastercard":
        return parse_mastercard_transactions(file)
    elif bank == "schwab":
        return parse_schwab_transactions(file)
    elif bank == "venmo":
        return parse_venmo_transactions(file)
