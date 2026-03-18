import csv
from datetime import datetime

FILE_PATH = "data/leads.csv"

def save_lead(lead):

    with open(FILE_PATH, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            lead["nome"],
            lead["telefone"],
            lead["cidade"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])