from argparse import ArgumentParser
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()

    parser = ArgumentParser()
    parser.add_argument("transactions_dir")
    args = parser.parse_args()
