from argparse import ArgumentParser
from dotenv import load_dotenv
from transactions import update_transactions_table


def main():
    parser = ArgumentParser()
    parser.add_argument("transactions_folder")
    args = parser.parse_args()
    transactions_folder = args.transactions_folder

    update_transactions_table(transactions_folder)


if __name__ == "__main__":
    load_dotenv()
    main()
