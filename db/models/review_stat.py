from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# ruff: noqa: F821
from db.models.base import Base


class ReviewStat(Base):
    __tablename__ = "review_stat"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"))
    course: Mapped["Course"] = relationship(back_populates="review_stat")

    satisfaction: Mapped[float] = mapped_column()  # 만족도 (1~5)
    workload: Mapped[float] = mapped_column()  # 학습량 (1~5)
    difficulty: Mapped[float] = mapped_column()  # 난이도 (1~5)
    delivery: Mapped[float] = mapped_column()  # 강의력 (1~5)
    achievement: Mapped[float] = mapped_column()  # 성취감 (1~5)
    grade: Mapped[float] = (
        mapped_column()
    )  # 학점 (1~5) - 1: 기대이하, 3: 보통, 5: 기대이상
    attendance: Mapped[float] = mapped_column()  # 출석 (1~5) - 1: 아예안함, 5: 매번함
