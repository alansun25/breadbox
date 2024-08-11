from argparse import ArgumentParser
from dotenv import load_dotenv
from src.functions import update_transactions_table


def main():
    parser = ArgumentParser()
    parser.add_argument("--folder")
    args = parser.parse_args()
    folder = args.folder

    load_dotenv()
    update_transactions_table(folder)


if __name__ == "__main__":
    main()
