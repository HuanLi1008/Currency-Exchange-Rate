from pymongo import MongoClient
import requests
from datetime import datetime, timedelta

import os
import certifi
import pika

# from dotenv import load_dotenv

def collect_data(base, target, period):

    # load_dotenv()
    mongodb_url = os.environ.get("MONGODB_URL")
    # print(mongodb_url)
    ca = certifi.where()
    # , tlsCAFile=ca
    client = MongoClient(mongodb_url)

    db = client['currency-exchange-rateDB']
    collection = db['rates']  
    api_url = 'https://api.frankfurter.app/'
    #API endpoint: https://api.frankfurter.app/2022-01-01..?from=CAD&to=CNY

    # receive three param from user: from, to, period
    #supported_currencies = {"AUD":"Australian Dollar","BGN":"Bulgarian Lev","BRL":"Brazilian Real","CAD":"Canadian Dollar","CHF":"Swiss Franc","CNY":"Chinese Renminbi Yuan","CZK":"Czech Koruna","DKK":"Danish Krone","EUR":"Euro","GBP":"British Pound","HKD":"Hong Kong Dollar","HUF":"Hungarian Forint","IDR":"Indonesian Rupiah","ILS":"Israeli New Sheqel","INR":"Indian Rupee","ISK":"Icelandic Króna","JPY":"Japanese Yen","KRW":"South Korean Won","MXN":"Mexican Peso","MYR":"Malaysian Ringgit","NOK":"Norwegian Krone","NZD":"New Zealand Dollar","PHP":"Philippine Peso","PLN":"Polish Złoty","RON":"Romanian Leu","SEK":"Swedish Krona","SGD":"Singapore Dollar","THB":"Thai Baht","TRY":"Turkish Lira","USD":"United States Dollar","ZAR":"South African Rand"}
    #choose any two different currencies and fetch data
    # base = "USD"
    # target = "CNY"
    # period = 365
    query = {"base": base, "target": target}

    if base == target:
        print("Base currency is same with target currency!")
        exit(1)
    #example of collection
    # {"base": A, "target": B, "start_date": "yyyy-mm-dd", "end_date": "yyyy-mm-dd", "rates": {"2023-11-23" : 1234, ……}}


    # check if data exsits in database
    result = collection.find_one(query)

    current = datetime.now()
    start_time = current - timedelta(days=period)
    time_format = "%Y-%m-%d"
    if result:
        if start_time.strftime(time_format) < result["start_date"]:  
            traverse_time = start_time   
            data_to_insert = {}  
            while traverse_time <= datetime.strptime(result["start_date"], time_format):
                curDate = traverse_time.strftime(time_format)
                traverse_time += timedelta(days=30)
                response = requests.get(api_url + curDate + ".." + traverse_time.strftime(time_format) + "?from=" +base + "&to=" + target).json()
                
                for key, value in response["rates"].items():
                    if key not in result["rates"]:
                        data_to_insert["rates." + key] = value[target]
            # collection.update_one(query, data_to_insert, upsert=True)
            collection.update_one(query, {"$set": {"start_date": (start_time).strftime(time_format), **data_to_insert}})
        if current.strftime(time_format) > result["end_date"]:
            traverse_time = datetime.strptime(result["end_date"], time_format)
            data_to_insert = {} 
            while traverse_time <= current:
                curDate = traverse_time.strftime(time_format)
                traverse_time += timedelta(days=30)

                response = requests.get(api_url + curDate + ".." + traverse_time.strftime(time_format) + "?from=" +base + "&to=" + target).json()
                if "message" in response and response["message"] == "not found": break
                for key, value in response["rates"].items():
                    if key not in result["rates"]:
                        data_to_insert["rates." + key] = value[target]
            collection.update_one(query, {"$set": {"end_date": (current).strftime(time_format), **data_to_insert}} )
        
    else:
        # first time fetch data from base currency to target currency
        traverse_time = start_time
        rates = {}
        while traverse_time <= current:
            curDate = traverse_time.strftime(time_format)
            traverse_time += timedelta(days=30)
            response = requests.get(api_url + curDate + ".." + traverse_time.strftime(time_format) + "?from=" +base + "&to=" + target).json()    
            if "rates" in response:
                for key, value in response["rates"].items():        
                    rates[key] = value[target]
        collection.insert_one({"base": base, "target": target, "start_date": start_time.strftime(time_format), "end_date": current.strftime(time_format), "rates": rates})

    #check data is stored in database
    # updated_data = collection.find_one(query)  
    # print(updated_data)

def consume():
    url = os.environ.get('CLOUDAMQP_URL')
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel() # start a channel
    channel.queue_declare(queue='collect_data') # Declare a queue
    def callback(ch, method, properties, body):
        print(" [x] Received " + str(body))
        collect_data(base=str(body)[:3], target=str(body)[3:6], period=int(str(body)[6:]))

    channel.basic_consume('1',
                        callback,
                        auto_ack=True)

    print(' [*] Waiting for messages:')
    channel.start_consuming()
    connection.close()



