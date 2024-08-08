from argparse import ArgumentParser
from dotenv import load_dotenv
from src.functions import update_transactions_table


def main():
    parser = ArgumentParser()
    parser.add_argument("transactions_folder")
    args = parser.parse_args()
    transactions_folder = args.transactions_folder

    load_dotenv()
    update_transactions_table(transactions_folder)


if __name__ == "__main__":
    main()
