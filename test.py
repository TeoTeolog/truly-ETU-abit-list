import json
import requests 
from datetime import datetime
import time

# def app():
#     last = ""

#     while True:
#         response2 = requests.get('https://lists.priem.etu.ru/public/list/76d72edb-bae7-4f5a-9d7b-fb85e3cb6c24')
#         data = json.loads(response2.text)

#         if last != "" and data["data"]["generated_at"] != last:
#             print(">>>>>>>>>>>>>>>>>>>>it's updating \nprev:", last,"\ncur:", data["data"]["generated_at"])
#             break 
#         else:
#             print('[',datetime.now().strftime("%H:%M:%S"),']', data["data"]["generated_at"])
#             last = data["data"]["generated_at"]
            
#         time.sleep(30)

import csv

def app():
    with open('eggs.csv', 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['Spam'] * 5 + ['Baked Beans'])
        spamwriter.writerow(['Spam', 'Lovely Spam', 'Wonderful Spam'])


app()