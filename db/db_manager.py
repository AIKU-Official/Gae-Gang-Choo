from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session

from .models.course import Course
from .models.review import Review

class DBMananger():
    def __init__(self, db_path: str, init_db: bool = False):
        self.engine = create_engine(f'sqlite:///{db_path}', echo=True)

        self.base = DeclarativeBase()
        if init_db:
            self.base.metadata.create_all(self.engine)

    def create_course(self, course: Course):
        with Session(self.engine) as session:
            session.add(course)
            session.commit()