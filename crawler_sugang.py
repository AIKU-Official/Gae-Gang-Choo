import time
from typing import List

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

from db.db_manager import DBMananger
from db.models.course import Course


class Crawler:
    def __init__(self, course_page_path: str, db_path: str):
        self.course_page_path = course_page_path
        self.db_path = db_path

    def crawl(self):
        if not self.course_page_path:
            self.load_courses()
        self.extract_info()

    def load_courses(self):
        """
        Load courses from the website and save the page source to a file.
        """
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        # Connect to the website and load courses
        driver.get("https://sugang.korea.ac.kr")
        time.sleep(3)
        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, "#Main"))
        try:
            notice = driver.find_element(By.CSS_SELECTOR, "#chkNoti")
            print("Notice found")
            notice.click()
            driver.implicitly_wait(1)
        except:
            print("Notice not found")

        driver.find_element(By.CSS_SELECTOR, "#menu_hakbu").click()
        driver.implicitly_wait(1)

        driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, "#coreMain"))
        driver.implicitly_wait(1)

        select_college = Select(driver.find_element(By.CSS_SELECTOR, "#pCol"))
        select_college.select_by_value("5720")  # 정보대학
        time.sleep(1)

        select_dept = Select(driver.find_element(By.CSS_SELECTOR, "#pDept"))
        select_dept.select_by_value("5722")  # 컴퓨터학과
        driver.implicitly_wait(1)

        driver.find_element(By.CSS_SELECTOR, "#btnSearch").click()
        time.sleep(3)

        lecture_elem = driver.find_element(By.CSS_SELECTOR, "#gridLecture > tbody")
        page_source = lecture_elem.get_attribute("innerHTML")
        print(page_source)

        with open("page_source.html", "w") as f:
            f.write(page_source)

        driver.quit()
        return

    def extract_info(self):
        """
        Extract course information from the page source and save it to the database.
        """
        page = open(self.course_page_path, "r").read()
        soup = BeautifulSoup(page, "html.parser")

        rows = soup.find_all("tr")

        courses: List[Course] = []
        for row in rows:
            cols = row.find_all("td")
            idx = [1, 2, 3, 4, 5, 6, 7, 8]
            name2idx = {
                "course_no": 1,
                "course_class": 2,
                "course_type": 3,
                "department": 4,
                "course_name": 5,
                "instructor": 6,
                "credit": 7,
                "room": 8,
            }
            course_info = {}
            for key, value in name2idx.items():
                course_info[key] = cols[value].text
                if key == "credit":
                    course_info[key] = int(course_info[key][0])
                elif key == "room":
                    time, room = self.parse_time_and_room(course_info[key])
                    course_info["timeslot"] = time
                    course_info["room"] = room

            # Skip courses without instructors
            if not course_info["instructor"]:
                continue

            course_info = self.load_details(course_info)
            course = Course(**course_info)
            db = DBMananger(self.db_path, init_db=True)

            courses.append(course)
        db.create_courses(courses)

    def load_details(self, course_info: dict) -> dict:
        """
        Load course details from the website.
        """
        url_base = "https://infodepot.korea.ac.kr/lecture1/lecsubjectPlanViewNew.jsp?year=2024&term=1R&grad_cd=0136&col_cd=9999&dept_cd={dept_code}&cour_cd={course_no}&cour_cls={course_class}&cour_nm=&std_id=&device=WW&language=ko"
        url = url_base.format(
            dept_code=5722,
            course_no=course_info["course_no"],
            course_class=course_info["course_class"],
        )
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        course_intro = soup.select_one(
            "body > div > div.page > form:nth-child(1) > div.bottom_view > table:nth-child(3) > tbody > tr:nth-child(2) > td"
        ).text
        course_info["course_intro"] = course_intro

        # Check if syllabus is available
        if "▶ 첨부파일" in page.text:
            print(course_info["course_name"], course_info["instructor"])
            print("No syllabus available.")
            return course_info

        prereq_1 = soup.select_one(
            "body > div > div.page > form:nth-child(1) > table:nth-child(29) > tbody > tr:nth-child(2) > td"
        ).text
        prereq_2 = soup.select_one(
            "body > div > div.page > form:nth-child(1) > table:nth-child(29) > tbody > tr:nth-child(4) > td"
        ).text
        course_info["prerequisite"] = prereq_1 + "\n" + prereq_2

        syllabus_table = soup.select_one(
            "body > div > div.page > form:nth-child(1) > table:nth-child(39) > tbody"
        )
        syllabus = ""
        max_weeks = 16
        for idx, row in enumerate(syllabus_table.find_all("tr")):
            if idx >= max_weeks:
                break
            week = row.find_all("td")[0].text.strip()
            content = row.find_all("td")[1].text.strip()
            syllabus += f"{week}: {content}\n"
        course_info["syllabus"] = syllabus

        return course_info

    def parse_time_and_room(self, text: str):
        if text == "":
            return "", ""

        lines = text.split("\n")
        timeslots = []
        timeslot_str = " ".join([line.split()[0] for line in lines])
        room_str = " ".join(lines[0].split()[1:]) if len(lines[0].split()) > 1 else ""

        return timeslot_str, room_str


if __name__ == "__main__":
    crawler = Crawler("page_source.html", db_path="course.db")
    crawler.crawl()
