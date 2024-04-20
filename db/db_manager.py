import json
from typing import List

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from db.models import Base, Course


class DBMananger:
    def __init__(self, db_path: str, init_db: bool = False):
        self.engine = create_engine(f"sqlite:///{db_path}")

        self.base = Base()
        if init_db:
            self.base.metadata.create_all(self.engine)

    def create_courses(self, course: List[Course]):
        with Session(self.engine) as session:
            session.add_all(course)
            session.commit()

    def read_courses(self):
        with Session(self.engine) as session:
            return session.scalars(select(Course)).all()

    def add_review_to_course(self, course, reviews, review_stat):
        with Session(self.engine) as session:
            course = session.get(Course, course.id)
            course.reviews = reviews
            course.review_stat = review_stat
            session.commit()

    def convert_to_json(self):
        with Session(self.engine) as session:
            courses = session.scalars(select(Course)).all()
            courses_dict = []
            for course in courses:
                course_dict = course.as_dict()
                if course.review_stat:
                    course_dict["review_stat"] = course.review_stat.as_dict()
                else:
                    print(
                        f"{course.course_name} - {course.instructor} does not have review_stat"
                    )

                course_dict["reviews"] = []
                for review in course.reviews:
                    review_dict = review.as_dict()
                    course_dict["reviews"].append(review_dict)
                courses_dict.append(course_dict)

            session.commit()

        courses_json = json.dumps(courses_dict, ensure_ascii=False, indent=4)
        return courses_json
