import sqlite3
import csv

def import_players():
    conn = sqlite3.connect("players.db")
    c = conn.cursor()

    with open("players.csv", "r") as file:
        reader = csv.DictReader(file)

        for row in reader:
            c.execute("""
                INSERT INTO players(name, age, position, speed)
                VALUES (?, ?, ?, ?)
            """, (row["name"], row["age"], row["position"], row["speed"]))

    conn.commit()
    conn.close()
    print("Import terminé ✔")

import_players()
