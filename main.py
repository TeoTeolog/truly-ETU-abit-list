import json
import requests
from datetime import datetime
import csv
from copy import deepcopy
import os

# 1 - бюджет, 2 - контракт
FIN_MODE = 1


class Student:
    def __init__(
        self, code, priority, has_original, enroll_condition, total_points, place
    ):
        self.code = code
        self.priority = priority
        self.has_original = has_original
        self.enroll_condition = enroll_condition
        self.total_points = total_points
        self.place = place

    def __str__(self):
        return [self.code, self.priority, self.total_points, self.place]

    def print(self):
        print([self.code, self.priority, self.total_points, self.place])


class Competition:
    def __init__(self, code, uuid):
        self.competition_code = code
        self.uuid = uuid
        self.competition_name = ""
        self.students_list = []
        self.total_num = 0

    def __str__(self):
        return [self.competition_code, self.competition_name, self.total_num]

    def add_students_data(self, students_list):
        for i in range(len(students_list)):
            student = students_list[i]
            self.add_student(
                [
                    student["code"],
                    student["priority"],
                    student["has_original"],
                    student["enroll_condition"],
                    student["total_points"],
                    i + 1,
                ]
            )

    def add_student(self, student):
        self.students_list.append(Student(*student))

    def add_data(self, data):
        self.add_students_data(data["list"])
        self.total_num = data["competition"]["total_num"]
        self.competition_name = data["competition"]["name"]

    def print(self):
        print([self.competition_code, self.competition_name, self.total_num])

    def find_student(self, student_code):
        for student in self.students_list:
            if student.code == student_code:
                return student
        return None


class App:
    def __init__(self):
        self.competition_list = []

    def __filter_nested_objects(self, external_list):
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
                            filtered_obj = Competition(code, nested_obj["uuid"])
                            result_list.append(filtered_obj)
        return result_list

    def __request_students_from_competition(self, competition):
        response = requests.get(
            "https://lists.priem.etu.ru/public/list/" + competition.uuid
        )
        data = json.loads(response.text)["data"]

        competition.add_data(data)

    def __export_to_csv(self, data_list, output_file):
        with open(output_file, "w", newline="") as csvfile:
            fieldnames = [
                "competition_code",
                "competition_name",
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
                total_num = obj.total_num
                competition_name = obj.competition_name
                competition_code = obj.competition_code
                i = 0
                for i in range(len(obj.students_list)):
                    item = obj.students_list[i]

                    writer.writerow(
                        {
                            "competition_code": competition_code,
                            "competition_name": competition_name,
                            "total_num": total_num,
                            "num": i + 1,
                            "code": item.code,
                            "priority": item.priority,
                            "has_original": item.has_original,
                            "total_points": item.total_points,
                        }
                    )

    def __find_student(self, all_rate_list, student_code, priority):
        student_was_found = False
        for competition_object in all_rate_list:
            student: Student = competition_object.find_student(student_code)
            if student and student.priority == priority:
                student_was_found = True
                if competition_object.total_num * 0.8 >= student.place:
                    return {
                        "student_code": student_code,
                        "competition_code": competition_object.competition_code,
                        "priority": priority,
                        "place": student.place,
                    }
        if student_was_found:
            return self.__find_student(all_rate_list, student_code, priority + 1)
        return None

    def __table_cleanup(self, all_rate_list):
        new_rate_list = deepcopy(all_rate_list)
        for competition_object in new_rate_list:
            competition_list = competition_object.students_list
            i = 0
            while i < len(competition_list):
                student = competition_list[i]
                successful_admission = self.__find_student(
                    new_rate_list, student.code, 1
                )
                if (
                    successful_admission
                    and successful_admission["competition_code"]
                    != competition_object.competition_code
                    or i + 1 >= competition_object.total_num * 0.8
                ):
                    competition_list.remove(student)
                else:
                    i += 1
        return new_rate_list

    def __estimate_min_score(self, all_rate_list):
        res = []
        for competition_object in all_rate_list:
            res.append(
                [
                    competition_object.students_list[
                        len(competition_object.students_list) - 1
                    ].total_points,
                    competition_object.competition_code,
                ]
            )
        return res

    def user_search_loop(self):
        choice = 1
        while choice != 0:
            print("0 - exit\n1 - find by code")
            choice = int(input())
            code = input()
            for competition in self.competition_list:
                student = competition.find_student(code)
                if student:
                    print(">>>>>")
                    competition.print()
                    student.print()
        return

    def estimate_min_score_all_rate(self):
        for estimate_score_item in self.__estimate_min_score(
            self.__table_cleanup(self.competition_list)
        ):
            print(estimate_score_item[1], ":", estimate_score_item[0])

    def parce_from_file(self, input_file):
        self.competition_list = []
        with open(input_file, "r") as csvfile:
            reader = csv.reader(csvfile)
            last_code = ""
            cur_competition = None
            for row in reader:
                if row[0] == "competition_code":
                    continue
                if last_code != row[0]:
                    if cur_competition and cur_competition.competition_code:
                        self.competition_list.append(cur_competition)
                    cur_competition = Competition(row[0], "none")
                    cur_competition.total_num = int(row[2])
                    cur_competition.competition_name = row[1]
                cur_competition.add_student(
                    [row[4], row[5], row[6], "None", float(row[7]), row[3]]
                )
                last_code = row[0]
            if cur_competition and cur_competition.competition_code:
                self.competition_list.append(cur_competition)

    def parce_dir(self, dir_path=""):
        content = os.listdir(dir_path)
        for index, name in enumerate(content, start=1):
            print(index, name)
        print("Enter num of file or full name (with extenshion):")
        choice = input()
        if choice in content:
            self.parce_from_file(content)
        elif int(choice) > 0 and int(choice) <= len(content):
            self.parce_from_file(content[int(choice) - 1])

    def save_to_file(self):
        self.__export_to_csv(
            self.__table_cleanup(self.competition_list),
            "res_scan_" + datetime.now().strftime("%m-%d-%Y-%H:%M") + "_.csv",
        )

    def parce_from_remote(self):
        response = requests.get("https://lists.priem.etu.ru/public/competitions/2/1")
        data = json.loads(response.text)["data"]

        self.competition_list = self.__filter_nested_objects(data["competition_groups"])

        loading_leng = len(self.competition_list)
        loading_cur = 0

        for competition in self.competition_list:
            self.__request_students_from_competition(competition)
            loading_cur += 1
            print(loading_cur, "/", loading_leng)


if __name__ == "__main__":
    app = App()
    # app.parce_from_remote()
    app.parce_dir(os.getcwd())
    app.save_to_file()
    app.estimate_min_score_all_rate()
    # app.parce_from_file("res_scan_07-27-2023-12:48_.csv")
    app.user_search_loop()
