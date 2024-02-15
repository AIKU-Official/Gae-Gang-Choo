from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import time
from sqlalchemy import select

from typing import List

from db.db_manager import DBMananger
from db.models.course import Course, Review, ReviewStat


class KLUECrawler:
    def __init__(self, page_dir: str, db_path: str, skip_crawling: bool = False):
        self.page_dir = page_dir
        self.db_path = db_path
        self.skip_crawling = skip_crawling
        self.db_manager = DBMananger(db_path)
        self.courses = self.db_manager.read_courses()
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        load_dotenv()

    def run(self):
        if not self.skip_crawling:
            self.crawl()

    def crawl(self):
        self.driver.get("https://klue.kr/login")
        self.driver.implicitly_wait(1)
        
        self.login()
        time.sleep(3)
        
        flag = False
        for course in self.courses:
            if course.course_no == "COSE401":
                flag = True
            if not flag:
                continue
            search_button = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/header/div/div/div[1]/a[1]')
            search_button.click()
            self.driver.implicitly_wait(3)
            time.sleep(1)

            course_no = course.course_no
            instructor = course.instructor
            query = course_no + " " + instructor
            print(query)

            try:
                self.search(query)
                time.sleep(3)
                reviews, review_stat = self.extract_reviews()

            except NoSuchElementException:
                print(f"No result found for {query}")
                continue

            self.db_manager.add_review_to_course(course, reviews, review_stat)

            time.sleep(60) # Wait due to server overload
        # self.extract_info()

    def search(self, query):
        search_box = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/section[1]/div/div/div/input')
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)
        
        first_result = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/section[2]/div/div/ul/div/div/li[1]')        
        first_result.click()
        time.sleep(3)

        # Scroll down to the bottom of the page (because the page is lazy-loaded)
        for i in range(10):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
        time.sleep(3)
        # Save the page source to a file
        # path = os.path.join("klue_sources", f"{query}.html")
        # with open(path, "w") as f:
        #     f.write(self.driver.page_source)
    
    def extract_reviews(self):
        review_elements = self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/section[3]/div/div/div[2]/div').find_elements(By.XPATH, "*")
        reviews: List[Review] = []

        grades = []
        grade_map = { "기대 이상": 5, "보통": 3, "기대 이하": 1 }

        attendance_map = { "매번함": 5, "자주함": 4, "종종함": 3, "거의안함": 2, "아예안함": 1}

        for review_element in review_elements:
            review_text = review_element.find_element(By.XPATH, "div/div/div[2]/div[1]").text
            
            grade_text = review_element.find_elements(By.XPATH, "div/div/div[2]/div[2]/span")[-1].text.replace("'", "")
            grade = grade_map[grade_text]
            grades.append(grade)
            
            reviews.append(Review(text=review_text))
            
        print("로드된 강의평 수: ", len(reviews), len(review_elements))

        satisfaction = float(self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/section[1]/div/div[3]/div/div[1]/div[1]/div[1]/span').text)
        attendance = float(attendance_map[self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/section[1]/div/div[3]/div/div[1]/div[2]/div/div[1]/span').text])
        workload = float(self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/section[1]/div/div[3]/div/div[1]/div[3]/div[1]/div[1]/div[1]/span[2]').text)
        difficulty = float(self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/section[1]/div/div[3]/div/div[1]/div[3]/div[1]/div[2]/div[1]/span[2]').text)
        delivery = float(self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/section[1]/div/div[3]/div/div[1]/div[3]/div[2]/div[1]/div[1]/span[2]').text)
        achievement = float(self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/section[1]/div/div[3]/div/div[1]/div[3]/div[2]/div[2]/div[1]/span[2]').text)
        grade = round(sum(grades) / len(grades), 1)

        print(f"만족도: {satisfaction}, 출석: {attendance}, 학습량: {workload}, 난이도: {difficulty}, 강의력: {delivery}, 성취감: {achievement}, 학점: {grade}")
        review_stat = ReviewStat(satisfaction=satisfaction, attendance=attendance, workload=workload, difficulty=difficulty, delivery=delivery, achievement=achievement, grade=grade)

        return reviews, review_stat
    
    def login(self):
        self.driver.find_element(By.XPATH,'//*[@id="root"]/div/div/div/div/div/div/input[1]').send_keys(os.getenv("KLUE_ID"))
        self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div/div/div/input[2]').send_keys(os.getenv("KLUE_PW"))
        self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div/div/div/button').click()
    

if __name__ == "__main__":
    crawler = KLUECrawler(page_dir="klue_sources", db_path="course.db", skip_crawling=False)
    crawler.crawl()
    # crawler.run()