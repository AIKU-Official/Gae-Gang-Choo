from sqlalchemy import select
from db.db_manager import DBMananger
from db.models.course import Course, Review, ReviewStat


if __name__ == "__main__":
    db_manager = DBMananger("course.db")
    json_db = db_manager.convert_to_json()

    with open("course.json", "w") as f:
        f.write(json_db)