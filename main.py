import json
import requests
from datetime import datetime
import csv
import os

# 1 - бюджет, 2 - контракт
FIN_MODE = 1


class Student_record:
    def __init__(
        self,
        student_code,
        priority,
        has_original,
        total_points,
        place,
    ):
        self.code = student_code
        self.priority = int(priority)
        self.has_original = has_original
        self.total_points = total_points
        self.place = place


class Competition:
    def __init__(self, code, name, total_num):
        self.code = code
        self.competition_name = name
        self.total_num = total_num
        self.students_list: [Student_record] = []

    def __str__(self):
        return str(
            [
                self.code,
                self.competition_name,
                self.total_num,
                len(self.students_list),
            ]
        )

    def add_students_data(self, students_list):
        for index, student_data in enumerate(students_list):
            student_data["place"] = index + 1
            self.students_list.append(
                Student_record(
                    student_data["code"],
                    student_data["priority"],
                    student_data["has_original"],
                    student_data["total_points"],
                    student_data["place"],
                )
            )

    def add_data(self, data):
        self.total_num = data["competition"]["total_num"]
        self.competition_name = data["competition"]["name"]
        self.add_students_data(data["list"])

    def find_student(self, code):
        for student in self.students_list:
            if student.code == code:
                return student
        return None


class All_store:
    def __default_succesful_rule(self, competition, place) -> bool:
        return competition.total_num * 0.2 >= place

    def __init__(self) -> None:
        self.values: [Competition] = []
        self.rule = self.__default_succesful_rule

    def parse_from_data(self, data: [{}]) -> None:
        for competition_data in data:
            competition = Competition(
                competition_data["code"],
                competition_data["name"],
                competition_data["total_num"],
            )
            competition.add_students_data(competition_data["list"])
            self.values.append(competition)

    def set_rule(self, rule: callable):
        self.rule = rule

    def get_by_code(self, code):
        for competition in self.values:
            if competition.code == code:
                return competition

    def __find_successful_admission(self, student_code, priority) -> Competition:
        student_was_found = False
        for competition in self.values:
            for index, record in enumerate(competition.students_list):
                if record.code == student_code and record.priority == priority:
                    if self.rule(competition, index + 1):
                        return competition
        if student_was_found:
            return self.__find_successful_admission(student_code, priority + 1)
        return None

    def table_cleanup(self):
        cur_all_rate_pos = 1
        all_rate_len = len(self.values)
        for competition_object in self.values:
            result = []
            for index, student in enumerate(competition_object.students_list):
                if (
                    self.__find_successful_admission(student.code, 1)
                    == competition_object
                ):
                    result.append(student)
                if index > competition_object.total_num:
                    break
            competition_object.students_list = result
            print(competition_object)
            print(
                [cur_all_rate_pos, "/", all_rate_len],
            )
            cur_all_rate_pos += 1


class Data_source:
    def get_all_tables(self) -> [Competition]:
        pass


class File_source(Data_source):
    def __get_file_name_from_dir(self, dir_path="") -> str:
        content = os.listdir(dir_path)
        for index, name in enumerate(content, start=1):
            print(index, name)
        print("Enter num of file or full name (with extenshion):")
        choice = input()
        if choice in content:
            return content
        elif int(choice) > 0 and int(choice) <= len(content):
            return content[int(choice) - 1]

    def get_all_tables(self) -> [Competition]:
        competition_list = []
        with open(self.__get_file_name_from_dir(os.getcwd()), "r") as csvfile:
            reader = csv.reader(csvfile)
            last_code = ""
            cur_competition = None
            for row in reader:
                if row[0] == "competition_code":
                    continue
                if last_code != row[0]:
                    if cur_competition:
                        competition_list.append(cur_competition)
                    cur_competition = {}
                    cur_competition["code"] = row[0]
                    cur_competition["total_num"] = int(row[2])
                    cur_competition["name"] = row[1]
                    cur_competition["list"] = []

                student_data = {}
                student_data["code"] = row[4]
                student_data["priority"] = row[5]
                student_data["has_original"] = row[6]
                student_data["total_points"] = float(row[7])
                student_data["place"] = row[3]

                cur_competition["list"].append(student_data)
                last_code = row[0]
            if cur_competition:
                competition_list.append(cur_competition)
        return competition_list


class Remote_source(Data_source):
    def __filter_nested_objects(self, external_list) -> [Competition]:
        result_list = []
        for external_obj in external_list:
            for nested_obj in external_obj["lists"]:
                if (
                    isinstance(nested_obj, dict)
                    and nested_obj["fin_source_id"] == FIN_MODE
                ):
                    filtered_obj = {}
                    filtered_obj["code"] = external_obj["code"]
                    filtered_obj["uuid"] = nested_obj["uuid"]
                    result_list.append(filtered_obj)

        return result_list

    def __request_students_from_competition(self, competition):
        response = requests.get(
            "https://lists.priem.etu.ru/public/list/" + competition["uuid"]
        )
        data = json.loads(response.text)["data"]
        result = {}
        result["code"] = competition["code"]
        result["name"] = data["competition"]["name"]
        result["total_num"] = data["competition"]["total_num"]
        result["list"] = data["list"]

        return result

    def get_all_tables(self) -> [Competition]:
        response = requests.get("https://lists.priem.etu.ru/public/competitions/2/1")
        data = json.loads(response.text)["data"]

        competition_links = self.__filter_nested_objects(data["competition_groups"])

        loading_leng = len(competition_links)
        loading_cur = 0

        competition_list = []

        for competition in competition_links:
            competition_list.append(
                self.__request_students_from_competition(competition)
            )
            loading_cur += 1
            print(loading_cur, "/", loading_leng)
        return competition_list


class File_Outstream:
    def out(self, store: All_store):
        self.__export_to_csv(
            "res_scan_" + datetime.now().strftime("%m-%d-%Y-%H:%M") + "_.csv",
            store.values,
        )

    def __export_to_csv(self, out_file_name: str, data_list: [Competition]) -> None:
        with open(out_file_name, "w", newline="") as csvfile:
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
                competition_code = obj.code
                for item in obj.students_list:
                    writer.writerow(
                        {
                            "competition_code": competition_code,
                            "competition_name": competition_name,
                            "total_num": total_num,
                            "num": item.place,
                            "code": item.code,
                            "priority": item.priority,
                            "has_original": item.has_original,
                            "total_points": item.total_points,
                        }
                    )


class App_extension:
    def __estimate_min_score(self, all_rate_list):
        res = []
        for competition_object in all_rate_list:
            res.append(
                [
                    competition_object.students_list[
                        len(competition_object.students_list) - 1
                    ].total_points,
                    competition_object.code,
                ]
            )
        return res

    def estimate_min_score_all_rate(self, store: All_store):
        for estimate_score_item in self.__estimate_min_score(store.values):
            print(estimate_score_item[1], ":", estimate_score_item[0])

    def user_search_loop(self, store: All_store):
        choice = 1
        while choice != 0:
            print("0 - exit\n1 - find by code")
            choice = int(input())
            code = input()
            for competition in store.values:
                student = competition.find_student(code)
                if student:
                    print(">>>>>")
                    competition.print()
                    student.print()
        return


class App:
    def __init__(self):
        self.store = All_store()

    def get_data(self, source: Data_source):
        self.store.parse_from_data(source.get_all_tables())

    def out_data(self, stream):
        stream.out(self.store)

    def clean_rate(self):
        self.store.table_cleanup()

    def execute_extention_capability(self, extention_capability):
        extention_capability(self.store)


if __name__ == "__main__":
    app = App()
    app.get_data(File_source())
    app.clean_rate()
    app.out_data(File_Outstream())
    app.execute_extention_capability(App_extension().estimate_min_score_all_rate)
    app.execute_extention_capability(App_extension().user_search_loop)
