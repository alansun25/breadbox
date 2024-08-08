BANKS = ["chase", "mastercard", "schwab", "venmo"]

COLNAMES = {
    "chase": [
        "transaction_date",
        "date",  # NOTE: Using post date rather than transaction date
        "merchant",
        "category",
        "type",
        "spend",
        "memo",
    ],
    "mastercard": [
        "date",
        "spend",
        "ignore1",
        "ignore2",
        "merchant",
    ],
    "schwab": [],
    "venmo": [],
}
