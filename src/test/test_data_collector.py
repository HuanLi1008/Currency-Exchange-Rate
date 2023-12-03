# import pytest
from pymongo import MongoClient
from src.main.data_collector import collect_data
from datetime import datetime
import os

def test_data_collector():
    collect_data("CAD", "CNY", 7)
    mongodb_url = os.environ.get("MONGODB_URL")
    client = MongoClient(mongodb_url)
    db = client['currency-exchange-rateDB']
    collection = db['rates'] 
    response = collection.find_one({"base": "CAD", "target": "CNY"})
    cur = datetime.now().strftime("%Y-%m-%d")
    assert response["end_date"] == cur
    assert response["start_date"] <= cur
    assert response["rates"] != {} 


