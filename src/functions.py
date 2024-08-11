from datetime import datetime
from src.classes import NotionClient, GroqClient, Transaction
import pandas as pd
import re

BANKS = ["chase", "mastercard", "schwab", "venmo"]
notion = NotionClient()


def get_iso_date(date: str):
    return datetime.strptime(date, "%m/%d/%Y").isoformat()[:10]


def create_transaction_object(
    merchant: str,
    spend: float,
    date: str,
    category: str = None,
    not_datetime: bool = True,
):
    if not_datetime:
        date = get_iso_date(date)
    else:
        date = date[:10]

    return Transaction(
        merchant=merchant,
        spend=spend,
        date=date,
        category=category,
    )


def parse_spend(spend_str: str):
    return float(re.sub(r"[^\d.]", "", spend_str))


def parse_chase(path: str):
    df = pd.read_csv(path)

    is_transaction = (df["Type"] == "Sale") & (df["Amount"] < 0)
    df = df[is_transaction]

    transactions = df.apply(
        lambda x: create_transaction_object(
            x["Description"],
            abs(x["Amount"]),
            x["Post Date"],
            x["Category"],
        ),
        axis=1,
    ).tolist()

    return transactions


def parse_mastercard(path: str):
    df = pd.read_csv(path, names=["date", "spend", "x", "y", "merchant"])

    # Ignoring rent payment which is auto-populated by Notion table already
    is_transaction = (df["spend"] < 0) & (~df["merchant"].str.contains("BPS*BILT", regex=False))
    df = df[is_transaction]

    transactions = df.apply(
        lambda x: create_transaction_object(
            x["merchant"],
            abs(x["spend"]),
            x["date"],
        ),
        axis=1,
    ).tolist()

    return transactions


def split_eversource(row: pd.Series):
    if "EVERSOURCE" in row["Description"]:
        row["Withdrawal"] = str(parse_spend(row["Withdrawal"]) / 4)
        
    return row


def parse_schwab(path: str):
    df = pd.read_csv(path)

    is_eversource = df["Description"].str.contains("EVERSOURCE", regex=False)
    is_transaction = (
        (df["Type"].str.contains("DEBIT", regex=False)) 
        | (df["Type"].str.contains("VISA", regex=False))
        ) | (is_eversource)
    df = df[is_transaction].apply(split_eversource, axis=1)

    transactions = df.apply(
        lambda x: create_transaction_object(
            x["Description"],
            parse_spend(x["Withdrawal"]),
            x["Date"],
        ),
        axis=1,
    ).tolist()
    
    return transactions


def add_venmo_repay(df: pd.Series, me: str):
    is_venmo_repay = ((df["Type"] == "Charge") & (df["From"] == me)) | (
        (df["Type"] == "Payment") & (df["To"] == me)
    )
    venmo_repayments = df[is_venmo_repay].to_dict(orient="records")
    repay_value = 0

    for repayment in venmo_repayments:
        repay_value += parse_spend(repayment["Amount (total)"])

    notion.add_venmo_repay(repay_value)


def parse_venmo(path: str):
    df = pd.read_csv(path, skiprows=[0, 1, 3])

    # Ignore Venmo payments for utilities and rent and anything
    # that isn't a payment or charge
    is_not_utilities_or_rent = (
        (~df["Note"].str.lower().str.contains("utilities", regex=False, na=False)) 
        & (~df["Note"].str.lower().str.contains("rent", regex=False, na=False))
    )
    is_payment_or_charge = (
        (df["Type"] == "Payment") 
        | (df["Type"] == "Charge")
    )
    df = df[is_not_utilities_or_rent & is_payment_or_charge]

    me = "Alan Sun"

    add_venmo_repay(df, me)

    is_transaction = ((df["Type"] == "Charge") & (df["To"] == me)) | (
        (df["Type"] == "Payment") & (df["From"] == me)
    )

    df = df[is_transaction]

    transactions = df.apply(
        lambda x: create_transaction_object(
            f"{x["Note"]} (venmo)",
            parse_spend(x["Amount (total)"]),
            x["Datetime"],
            not_datetime=False,
        ),
        axis=1,
    ).tolist()

    return transactions

def parse_transactions(folder: str, bank: str):
    path = f"{folder}/{bank}.csv"

    transactions: list[Transaction] = []
    match bank:
        case "chase":
            transactions.extend(parse_chase(path))
        case "mastercard":
            transactions.extend(parse_mastercard(path))
        case "schwab":
            transactions.extend(parse_schwab(path))
        case "venmo":
            transactions.extend(parse_venmo(path))

    return transactions


def get_parsed_transactions(folder: str):
    parsed_transactions = []
    for bank in BANKS:
        transactions = parse_transactions(folder, bank)
        parsed_transactions.extend(transactions)

    return parsed_transactions


def update_transactions_table(folder: str):
    groq = GroqClient(notion.get_categories())

    parsed_transactions = get_parsed_transactions(folder)
    categorized_transactions = groq.categorize_transactions(parsed_transactions)
    notion.add_transactions(categorized_transactions)
