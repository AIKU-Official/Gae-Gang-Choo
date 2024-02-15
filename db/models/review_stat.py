from typing import List, Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .base import Base

class ReviewStat(Base):
    __tablename__ = "review_stat"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"))
    course: Mapped["Course"] = relationship(back_populates="review_stat")

    satisfaction: Mapped[float] = mapped_column() # 만족도 (1~5)
    workload: Mapped[float] = mapped_column() # 학습량 (1~5)
    difficulty: Mapped[float] = mapped_column() # 난이도 (1~5)
    delivery: Mapped[float] = mapped_column() # 강의력 (1~5)
    achievement: Mapped[float] = mapped_column() # 성취감 (1~5)
    grade: Mapped[float] = mapped_column() # 학점 (1~5)
    attendance: Mapped[float] = mapped_column() # 출석 (1~5)