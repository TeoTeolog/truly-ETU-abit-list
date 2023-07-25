import json
import requests 
from datetime import datetime
import csv

# 1 - бюджет, 2 - контракт
FIN_MODE = 1

def app():

    def filter_nested_objects(external_list):
        result_list = []
        for external_obj in external_list:
            code = external_obj['code']
            if code is not None and isinstance(code, str):
                for nested_obj in external_obj['lists']:
                    if isinstance(nested_obj, dict) and nested_obj['fin_source_id'] == FIN_MODE:
                        uuid = nested_obj.get('uuid')
                        if uuid is not None and isinstance(uuid, str):
                            filtered_obj = {'code': code, 'uuid': uuid}
                            result_list.append(filtered_obj)
        return result_list
    
    def request_students_from_competition(competition):

        response = requests.get('https://lists.priem.etu.ru/public/list/'+competition["uuid"])

        data = json.loads(response.text)["data"]

        students_list = data["list"]

        result_list = []
        
        for external_obj in students_list:
            filtered_obj = {'code': external_obj['code'], 'priority': external_obj['priority'], "has_original":external_obj['has_original'], "enroll_condition": external_obj["enroll_condition"]}
            result_list.append(filtered_obj)
        
        return {"competition_code": competition["code"], "generated_at": data["generated_at"],"total_num": data["competition"]["total_num"], "list": result_list}


    def print_list(arr):    
        print('[-------------')
        for i in arr:
            print(i)
        print('-------------]')

    def export_to_csv(data_list, output_file):
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ["competition_code",'code', 'priority', 'has_original', 'total_num']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for obj in data_list:
                total_num = obj['total_num']
                competition_code = obj['competition_code']
                lists = obj['list']
                for item in lists:
                    code = item['code']
                    priority = item['priority']
                    has_original = item['has_original']

                    writer.writerow({
                        "competition_code": competition_code,
                        'code': code,
                        'priority': priority,
                        'has_original': has_original,
                        'total_num': total_num
                    })

   
    response = requests.get('https://lists.priem.etu.ru/public/competitions/2/1')

    data = json.loads(response.text)["data"]

    competition_list = filter_nested_objects(data["competition_groups"])

    print_list(competition_list)

    all_competition_rate_list = []

    loading_leng = len(competition_list)
    loading_cur = 0

    for competition in competition_list:
        students_object = request_students_from_competition(competition)
        all_competition_rate_list.append(students_object)
        loading_cur+=1
        print(loading_cur,'/',loading_leng)

    export_to_csv(all_competition_rate_list,'res_scan_'+datetime.now().strftime("%m-%d-%Y-%H:%M")+'_.csv')

app()