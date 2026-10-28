"""题目讨论区接口。"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, get_current_user_optional
from ..models import Challenge, Comment, CompetitionChallenge, User
from ..schemas import CommentIn, CommentListOut, CommentOut

router = APIRouter(prefix="/comments", tags=["comments"])
TargetType = Literal["challenge", "competition"]


def _target_filter(target_type: TargetType, target_id: int):
    if target_type == "challenge":
        return Comment.challenge_id == target_id
    return Comment.competition_challenge_id == target_id


def _ensure_target(db: Session, target_type: TargetType, target_id: int) -> None:
    if target_type == "challenge":
        target = db.get(Challenge, target_id)
        if target is None or target.status != "published":
            raise HTTPException(status_code=404, detail="题目不存在或未上架")
        return
    if db.get(CompetitionChallenge, target_id) is None:
        raise HTTPException(status_code=404, detail="比赛题目不存在")


@router.get("/{target_type}/{target_id}", response_model=CommentListOut)
def list_comments(
    target_type: TargetType,
    target_id: int,
    current: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    _ensure_target(db, target_type, target_id)
    query = db.query(Comment).filter(_target_filter(target_type, target_id))
    total = query.count()
    rows = (
        query.join(User, User.id == Comment.user_id)
        .add_columns(User.username, User.role)
        .order_by(Comment.created_at.desc(), Comment.id.desc())
        .limit(100)
        .all()
    )
    return CommentListOut(
        total=total,
        items=[
            CommentOut(
                id=comment.id,
                username=username,
                role=role,
                content=comment.content,
                created_at=comment.created_at,
                is_mine=bool(current and comment.user_id == current.id),
            )
            for comment, username, role in rows
        ],
    )


@router.post(
    "/{target_type}/{target_id}",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    target_type: TargetType,
    target_id: int,
    body: CommentIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_target(db, target_type, target_id)
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="评论内容不能为空")
    comment = Comment(
        user_id=current.id,
        challenge_id=target_id if target_type == "challenge" else None,
        competition_challenge_id=target_id if target_type == "competition" else None,
        content=content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return CommentOut(
        id=comment.id,
        username=current.username,
        role=current.role,
        content=comment.content,
        created_at=comment.created_at,
        is_mine=True,
    )


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    if comment.user_id != current.id and current.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除该评论")
    db.delete(comment)
    db.commit()
    return {"success": True}
