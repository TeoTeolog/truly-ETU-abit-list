import json
import requests
from datetime import datetime
import csv

# from copy import deepcopy
import os

# 1 - бюджет, 2 - контракт
FIN_MODE = 1


class Student_record:
    def __init__(
        self,
        priority,
        has_original,
        total_points,
        place,
    ):
        self.priority = int(priority)
        self.has_original = has_original
        self.total_points = total_points
        self.place = place

    def __str__(self):
        return [self.code, self.priority, self.total_points, self.place]


class Student:
    def __init__(self, code):
        self.code = code
        self.records: {str: Student_record} = []

    def __str__(self):
        return [self.code, self.priority, self.total_points, self.place]

    def add_record(self, competition, priority, has_original, total_points, place):
        self.records[competition.code] = Student_record(
            competition, priority, has_original, total_points, place
        )

    def get_record_by_competition(self, competition_code) -> Student_record:
        return self.records[str(competition_code)]

    def get_all_record(self) -> Student_record:
        return [item for item in self.records]

    def get_records_ordered_by_priority(self) -> [Student_record]:
        result: [Student_record] = []
        for record in self.records:
            result[record.priority - 1] = record
        return result

    def remove_record(self, record):
        self.records.remove(record)


class All_Student_Table:
    def __init__(self):
        self.students_list: [Student] = []
        self.total_num = 0

    def __str__(self):
        return [self.students_list]

    def update_or_add_student(self, student_data) -> Student:
        student: Student = None
        for student_item in self.students_list:
            if student_item == student_data["code"]:
                student = student_item
                break
        if not student:
            student = Student(student_data["code"])
            self.students_list.append(student)

        student.add_record(
            student_data["competition_code"],
            student_data["priority"],
            student_data["has_original"],
            student_data["total_points"],
            student_data["place"],
        )
        return student


class Table:
    def __init__(self, code, uuid):
        self.code = code
        self.uuid = uuid
        self.competition_name = ""
        self.students_list: [Student] = []
        self.total_num = 0

    def __str__(self):
        return [self.code, self.competition_name, self.total_num]

    def __add_student(self, student):
        self.students_list.append(student)

    def add_students_data(self, students_list, data_transformer: callable):
        for index, student_data in enumerate(students_list):
            student_data["competition_code"] = self.code
            student_data["place"] = index + 1
            self.__add_student(data_transformer(student_data))

    def add_data(self, data, data_transformer: callable):
        self.total_num = data["competition"]["total_num"]
        self.competition_name = data["competition"]["name"]
        self.add_students_data(data["list"], data_transformer)


class All_tables:
    def __init__(self):
        self.tables: [Table] = []

    def __init__(self, tables: [Table]):
        self.tables = tables

    def set_tables(self, tables):
        self.tables = tables

    def get_competition_by_code(self, code):
        for table in self.tables:
            if table.code == code:
                return table


class Data_source:
    def __init__(self):
        self.data

    def get_all_tables(self) -> (All_Student_Table, [Table]):
        pass

    # def get_data(self, student_table: All_Student_Table, tables: All_tables):
    #     student_data, competition_data = self.get_all_tables()
    #     tables.set_tables(competition_data)
    #     student_table = student_data


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

    def get_all_tables(self) -> (All_Student_Table, [Table]):
        competition_list = []
        all_students_table = All_Student_Table()
        with open(self.__get_file_name_from_dir(os.getcwd()), "r") as csvfile:
            reader = csv.reader(csvfile)
            last_code = ""
            cur_competition = None
            for row in reader:
                if row[0] == "competition_code":
                    continue
                if last_code != row[0]:
                    if cur_competition and cur_competition.code:
                        competition_list.append(cur_competition)
                    cur_competition = Table(row[0], "none")
                    cur_competition.total_num = int(row[2])
                    cur_competition.competition_name = row[1]

                student_data = {}
                student_data["competition_code"] = row[4]
                student_data["priority"] = row[5]
                student_data["has_original"] = row[6]
                student_data["total_points"] = float(row[7])
                student_data["place"] = row[3]

                cur_competition.add_student(
                    all_students_table.update_or_add_student(student_data)
                )
                last_code = row[0]
            if cur_competition and cur_competition.code:
                competition_list.append(cur_competition)
        return (all_students_table, competition_list)


class Remote_source(Data_source):
    def __filter_nested_objects(self, external_list) -> [Table]:
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
                            filtered_obj = Table(code, nested_obj["uuid"])
                            result_list.append(filtered_obj)
        return result_list

    def __request_students_from_competition(self, all_students_table, competition):
        response = requests.get(
            "https://lists.priem.etu.ru/public/list/" + competition.uuid
        )
        data = json.loads(response.text)["data"]

        competition.add_data(data, all_students_table.update_or_add_student)

    def get_all_tables(self) -> (All_Student_Table, [Table]):
        response = requests.get("https://lists.priem.etu.ru/public/competitions/2/1")
        data = json.loads(response.text)["data"]

        competition_list = self.__filter_nested_objects(data["competition_groups"])
        all_student_table = All_Student_Table()

        loading_leng = len(competition_list)
        loading_cur = 0

        for competition in competition_list:
            self.__request_students_from_competition(all_student_table, competition)
            loading_cur += 1
            print(loading_cur, "/", loading_leng)
        return (all_student_table, competition_list)


class App:
    def __init__(self):
        self.competition_list = All_tables()
        self.all_students_list: [Student] = []

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
                competition_code = obj.code
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

    # def equip_rules(self) -> bool:
    #     return record.place < self.competition_list.get_competition_by_code(record.)

    def __find_successful_admission(self, rules, student: Student) -> Table:
        for record in student.get_records_ordered_by_priority():
            if rules(record):
                return record.competition
        return None

    def clear_all_table(self):
        for table in self.competition_list:
            result = []
            for index, student in enumerate(table):
                if self.__find_successful_admission(self.equip_rules, student) == table:
                    result.append(student)
                if index > table.total_num:
                    break
            table = result

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

    # rewrite
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

    def save_to_file(self):
        self.__export_to_csv(
            self.__table_cleanup(self.competition_list),
            "res_scan_" + datetime.now().strftime("%m-%d-%Y-%H:%M") + "_.csv",
        )

    def get_source(self, data_source: Data_source):
        self.tables = data_source.get_all_tables()


if __name__ == "__main__":
    app = App()
    # app.parce_from_remote()
    app.parce_dir(os.getcwd())
    app.save_to_file()
    app.estimate_min_score_all_rate()
    # app.parce_from_file("res_scan_07-27-2023-12:48_.csv")
    app.user_search_loop()
