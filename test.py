import json
import requests
from datetime import datetime
import time
import csv


# def app():
#     last = ""

#     while True:
#         response2 = requests.get(
#             "https://lists.priem.etu.ru/public/list/76d72edb-bae7-4f5a-9d7b-fb85e3cb6c24"
#         )
#         data = json.loads(response2.text)

#         if last != "" and data["data"]["generated_at"] != last:
#             print(
#                 ">>>>>>>>>>>>>>>>>>>>it's updating \nprev:",
#                 last,
#                 "\ncur:",
#                 data["data"]["generated_at"],
#             )
#             break
#         else:
#             print(
#                 "[",
#                 datetime.now().strftime("%H:%M:%S"),
#                 "]",
#                 data["data"]["generated_at"],
#             )
#             last = data["data"]["generated_at"]

#         time.sleep(30)


# def app():
#     with open("eggs.csv", "w", newline="") as csvfile:
#         spamwriter = csv.writer(
#             csvfile, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL
#         )
#         spamwriter.writerow(["Spam"] * 5 + ["Baked Beans"])
#         spamwriter.writerow(["Spam", "Lovely Spam", "Wonderful Spam"])


class A:
    def do(self):
        print("Do")


class B:
    def test(self, a):
        a()


def app():
    # test = {"jopa": 1, "jupa": 2, "koga": 99}
    b = B()
    a = A()
    b.test(a.do)
    # for value, key in enumerate(test):
    #     print(value, key)


app()
