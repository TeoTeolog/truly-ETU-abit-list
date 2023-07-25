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
            code = external_obj["code"]
            if code is not None and isinstance(code, str):
                for nested_obj in external_obj["lists"]:
                    if (
                        isinstance(nested_obj, dict)
                        and nested_obj["fin_source_id"] == FIN_MODE
                    ):
                        uuid = nested_obj.get("uuid")
                        if uuid is not None and isinstance(uuid, str):
                            filtered_obj = {"code": code, "uuid": uuid}
                            result_list.append(filtered_obj)
        return result_list

    def request_students_from_competition(competition):
        response = requests.get(
            "https://lists.priem.etu.ru/public/list/" + competition["uuid"]
        )

        data = json.loads(response.text)["data"]

        students_list = data["list"]

        result_list = []

        for external_obj in students_list:
            filtered_obj = {
                "code": external_obj["code"],
                "priority": external_obj["priority"],
                "has_original": external_obj["has_original"],
                "enroll_condition": external_obj["enroll_condition"],
                "total_points": external_obj["total_points"],
            }
            result_list.append(filtered_obj)

        return {
            "competition_code": competition["code"],
            "generated_at": data["generated_at"],
            "total_num": data["competition"]["total_num"],
            "list": result_list,
        }

    def print_list(arr):
        print("[-------------")
        for i in arr:
            print(i)
        print("-------------]")

    def export_to_csv(data_list, output_file):
        with open(output_file, "w", newline="") as csvfile:
            fieldnames = [
                "competition_code",
                "total_num",
                "num",
                "code",
                "priority",
                "has_original",
                "total_points",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for obj in data_list:
                total_num = obj["total_num"]
                competition_code = obj["competition_code"]
                lists = obj["list"]
                i = 0
                for i in range(len(lists)):
                    item = lists[i]
                    code = item["code"]
                    priority = item["priority"]
                    has_original = item["has_original"]
                    total_points = item["total_points"]
                    writer.writerow(
                        {
                            "competition_code": competition_code,
                            "total_num": total_num,
                            "num": i + 1,
                            "code": code,
                            "priority": priority,
                            "has_original": has_original,
                            "total_points": total_points,
                        }
                    )

    def find_student(all_rate_list, student_code, priority):
        student_was_found = False
        for competition_object in all_rate_list:
            competition_list = competition_object["list"]
            for i in range(len(competition_list)):
                student = competition_list[i]
                if student_code == student["code"] and student["priority"] == priority:
                    student_was_found = True
                    if competition_object["total_num"] * 0.8 >= i + 1:
                        return {
                            "student_code": student_code,
                            "competition_code": competition_object["competition_code"],
                            "priority": priority,
                            "place": i,
                        }
        if student_was_found:
            return find_student(all_rate_list, student_code, priority + 1)
        return None

    def table_cleanup(all_rate_list):
        all_rate_len = len(all_rate_list)
        cur_all_rate_pos = 0

        for competition_object in all_rate_list:
            competition_list = competition_object["list"]

            i = 0
            while i < len(competition_list):
                student = competition_list[i]
                successful_admission = find_student(all_rate_list, student["code"], 1)
                if (
                    successful_admission
                    and successful_admission["competition_code"]
                    != competition_object["competition_code"]
                    or i + 1 >= competition_object["total_num"] * 0.8
                ):
                    competition_list.remove(student)
                else:
                    i += 1

            print(">>>>>>>>>>>>>", [cur_all_rate_pos, "/", all_rate_len])
            cur_all_rate_pos += 1

    def estimate_min_score(all_rate_list):
        res = []
        for competition_object in all_rate_list:
            res.append(
                [
                    competition_object["list"][len(competition_object["list"]) - 1][
                        "total_points"
                    ],
                    competition_object["competition_code"],
                ]
            )
        return res

    response = requests.get("https://lists.priem.etu.ru/public/competitions/2/1")
    data = json.loads(response.text)["data"]

    competition_list = filter_nested_objects(data["competition_groups"])

    print_list(competition_list)

    all_competition_rate_list = []

    loading_leng = len(competition_list)
    loading_cur = 0

    for competition in competition_list:
        students_object = request_students_from_competition(competition)
        all_competition_rate_list.append(students_object)
        loading_cur += 1
        print(loading_cur, "/", loading_leng)

    table_cleanup(all_competition_rate_list)

    export_to_csv(
        all_competition_rate_list,
        "res_scan_" + datetime.now().strftime("%m-%d-%Y-%H:%M") + "_.csv",
    )

    for estimate_score_item in estimate_min_score(all_competition_rate_list):
        print(estimate_score_item[1], ":", estimate_score_item[0])


app()
