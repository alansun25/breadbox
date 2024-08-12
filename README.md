# Breadbox

LLM-powered financial assistant built for budgeting in Notion.

Features:

- Parses bank CSVs into a standardized transaction format.
- Categorizes transactions using a Llama3 LLM.
- Records Venmo payments to and from the user.
- Tracks income from paychecks.
- Uploads all data into the connected Notion finance page.

Built with:

- Python
- pandas
- [notion-sdk-py](https://github.com/ramnes/notion-sdk-py)
- [Groq LLM API](https://groq.com/)

_Note: This code works specifically for my own financial tracking purposes, e.g. my banks, my Notion table schemas, etc. Future work could be done to generalize functionality and package this with a Notion finance tracking template._
