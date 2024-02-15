from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session
from sqlalchemy import select

from typing import List

from .models import Base
from .models import Course
from .models import ReviewStat
from .models import Review

class DBMananger():
    def __init__(self, db_path: str, init_db: bool = False):
        self.engine = create_engine(f'sqlite:///{db_path}')

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
        

if __name__ == "__main__":
    db_manager = DBMananger("course.db", init_db=True)
    print(db_manager.read_courses())