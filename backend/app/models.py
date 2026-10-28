"""数据模型。"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    solves: Mapped[list["SolveRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Challenge(Base):
    """题目模型。"""

    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5 星
    points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    attachment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    flag: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(50), default="admin", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="published", nullable=False)  # published/pending/draft/rejected
    solved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    solves: Mapped[list["SolveRecord"]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )


class SolveRecord(Base):
    """解题记录。"""

    __tablename__ = "solve_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), index=True, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    solved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="solves")
    challenge: Mapped["Challenge"] = relationship(back_populates="solves")


class Favorite(Base):
    """用户收藏的题库题目。"""

    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="uq_favorite_user_challenge"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("challenges.id"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Comment(Base):
    """题目讨论区评论，可关联题库题目或比赛真题。"""

    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint(
            "(challenge_id IS NOT NULL AND competition_challenge_id IS NULL) OR "
            "(challenge_id IS NULL AND competition_challenge_id IS NOT NULL)",
            name="ck_comment_single_target",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    challenge_id: Mapped[int | None] = mapped_column(
        ForeignKey("challenges.id"), index=True, nullable=True
    )
    competition_challenge_id: Mapped[int | None] = mapped_column(
        ForeignKey("competition_challenges.id"), index=True, nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship()


class Friendship(Base):
    """好友关系：pending 表示待接受，accepted 表示已成为好友。"""

    __tablename__ = "friendships"
    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_friendship_pair"),
        CheckConstraint("requester_id != addressee_id", name="ck_friendship_not_self"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    addressee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class DirectMessage(Base):
    """好友之间的一对一私信。"""

    __tablename__ = "direct_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Article(Base):
    """公告 / 文章。"""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="article", index=True, nullable=False)  # article / announcement
    author: Mapped[str] = mapped_column(String(50), default="admin", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Notification(Base):
    """站内通知：题目提交、审核结果等。"""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    related_challenge_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    related_article_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Competition(Base):
    """比赛（如长城杯、强网杯）。"""

    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    icon: Mapped[str] = mapped_column(String(10), default="🏆", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    editions: Mapped[list["CompetitionEdition"]] = relationship(
        back_populates="competition", cascade="all, delete-orphan"
    )


class CompetitionEdition(Base):
    """比赛届次（如 2024 第一届长城杯）。"""

    __tablename__ = "competition_editions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # 如 "2024 第一届"
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    competition: Mapped["Competition"] = relationship(back_populates="editions")
    challenges: Mapped[list["CompetitionChallenge"]] = relationship(
        back_populates="edition", cascade="all, delete-orphan"
    )


class CompetitionChallenge(Base):
    """比赛题目（某一届下的具体题目）。"""

    __tablename__ = "competition_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    edition_id: Mapped[int] = mapped_column(ForeignKey("competition_editions.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="Web", nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    flag: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    attachment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    solved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    edition: Mapped["CompetitionEdition"] = relationship(back_populates="challenges")


class CompetitionSolve(Base):
    """比赛题目解题记录（与题库题目分开统计）。"""

    __tablename__ = "competition_solves"
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="uq_competition_solve_user_challenge"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("competition_challenges.id"), index=True, nullable=False
    )
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    solved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
