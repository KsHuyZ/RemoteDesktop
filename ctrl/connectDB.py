import collections
from http import client
from sqlite3 import connect
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())
connect_string = os.environ.get("DB_URL")
client = MongoClient(connect_string)
dbs = client.list_database_names()
DB = client.RemoteDesktop
collections = DB.list_collection_names()

print(collections)
