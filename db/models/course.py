from typing import List, Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .base import Base
from .review_stat import ReviewStat
from .review import Review

class Course(Base):
    __tablename__ = 'course'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_name: Mapped[str] = mapped_column(String(30))
    course_no: Mapped[str] = mapped_column(String(10))
    course_class: Mapped[str] = mapped_column(String(10))
    department: Mapped[str] = mapped_column(String(30))
    credit: Mapped[int] = mapped_column()
    course_type: Mapped[str] = mapped_column(String(10))
    instructor: Mapped[str] = mapped_column(String(30))
    timeslot: Mapped[Optional[str]] = mapped_column(String(30))
    room: Mapped[Optional[str]] = mapped_column(String(30))
    course_intro: Mapped[Optional[str]] = mapped_column(String(100))
    prerequisite: Mapped[Optional[str]] = mapped_column(String(100))
    syllabus: Mapped[Optional[str]] = mapped_column(String(1000))
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="course", cascade="all, delete-orphan")
    review_stat: Mapped["ReviewStat"] = relationship(back_populates="course")