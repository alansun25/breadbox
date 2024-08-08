from argparse import ArgumentParser
from dotenv import load_dotenv
from src.functions import update_transactions_table


def main():
    parser = ArgumentParser()
    parser.add_argument("--folder_path")
    args = parser.parse_args()
    folder_path = args.folder_path

    load_dotenv()
    update_transactions_table(folder_path)


if __name__ == "__main__":
    main()
