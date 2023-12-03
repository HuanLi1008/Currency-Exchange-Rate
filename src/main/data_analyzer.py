from pymongo import MongoClient
import os
import certifi
from datetime import datetime, timedelta

def analyz(rates):
    return {"min" : min(rates), "max": max(rates), "average": sum(rates) / len(rates)}

def data_analyzer(base, target, period):
    mongodb_url = os.environ.get("MONGODB_URL")
    ca = certifi.where()
    # tlsCAFile=ca
    # client = MongoClient(mongodb_url, )
    client = MongoClient(mongodb_url)
    db = client['currency-exchange-rateDB']
    collection = db['rates'] 

    query = {"base": base, "target": target}
    allrates = collection.find_one(query)
     
    start_time = (datetime.now() - timedelta(days=period)).strftime("%Y-%m-%d")
    date_rate = []
    for key, val in allrates["rates"].items():
        if key < start_time: continue
        date_rate.append([key, val])
    date_rate.sort()
    dates, rates = zip(*date_rate[:])
    dic = analyz(rates)
    dic["dates"] = dates
    dic["rates"] = rates
    return dic

# data_analyzer("CNY", "CAD", 10)