from argparse import ArgumentParser
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from src.functions import update_transactions_table


def main():
    parser = ArgumentParser()
    parser.add_argument("--folder")
    args = parser.parse_args()
    folder = args.folder

    if folder is None:
        # Default to previous month
        now = datetime.now()
        previous_month = now - relativedelta(months=1)
        month_string = previous_month.strftime("%Y-%m")
        folder = f"transactions/{month_string}"

    print(f"Using folder {folder}.")

    load_dotenv()
    update_transactions_table(folder)


if __name__ == "__main__":
    main()
