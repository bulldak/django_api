import pandas as pd
import sqlite3

# Read csv file.
df = pd.read_csv("data_info.csv")

# Connect to (create) database.
database = "db.sqlite3"
conn = sqlite3.connect(database)
dtype={
    "contentsid": "TextField",
    "kakaoid": "TextField",
    "category": "TextField",
    "title": "TextField",
    "alltag": "TextField",
    "tag": "TextField",
    "address": "TextField",
    "latitude": "TextField",
    "longitude": "TextField",
    "thumbnail": "TextField",
    "star": "TextField",
    "starnum": "IntegerField"
}
df.to_sql(name='api_place_info', con=conn, if_exists='replace', dtype=dtype, index=True, index_label="id")
conn.close()

df = pd.read_csv("data_keywords.csv")

# Connect to (create) database.
database = "db.sqlite3"
conn = sqlite3.connect(database)
dtype={
    "contentsid": "TextField",
    "kakaoid": "TextField",
    "category": "TextField",
    "experience": "IntegerField",
    "activity": "IntegerField",
    "nature": "IntegerField",
    "beach": "IntegerField",
    "rest": "IntegerField",
    "photo": "IntegerField",
    "parents": "IntegerField",
    "children": "IntegerField",
    "friends": "IntegerField",
}
df.to_sql(name='api_place_keywords', con=conn, if_exists='replace', dtype=dtype, index=True, index_label="id")
conn.close()