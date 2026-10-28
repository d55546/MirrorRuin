"""好友申请与一对一私信接口。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import DirectMessage, Friendship, User
from ..schemas import (
    DirectMessageIn,
    DirectMessageListOut,
    DirectMessageOut,
    FriendOut,
    FriendRequestIn,
    FriendRequestOut,
    SocialOverviewOut,
    SocialUserOut,
)

router = APIRouter(prefix="/social", tags=["social"])


def _pair_filter(left_id: int, right_id: int):
    return or_(
        (Friendship.requester_id == left_id) & (Friendship.addressee_id == right_id),
        (Friendship.requester_id == right_id) & (Friendship.addressee_id == left_id),
    )


def _friendship_between(db: Session, left_id: int, right_id: int) -> Friendship | None:
    return db.query(Friendship).filter(_pair_filter(left_id, right_id)).first()


def _social_user(user: User) -> SocialUserOut:
    return SocialUserOut(id=user.id, username=user.username, role=user.role)


def _request_out(item: Friendship, user: User) -> FriendRequestOut:
    return FriendRequestOut(id=item.id, user=_social_user(user), created_at=item.created_at)


def _require_friend(db: Session, current: User, friend_id: int) -> User:
    if friend_id == current.id:
        raise HTTPException(status_code=400, detail="不能给自己发消息")
    friend = db.get(User, friend_id)
    if friend is None or not friend.is_active:
        raise HTTPException(status_code=404, detail="用户不存在")
    relation = _friendship_between(db, current.id, friend_id)
    if relation is None or relation.status != "accepted":
        raise HTTPException(status_code=403, detail="只有好友之间才能发送私信")
    return friend


@router.get("/search", response_model=list[SocialUserOut])
def search_users(
    q: str = Query(min_length=1, max_length=50),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    keyword = q.strip()
    if not keyword:
        return []
    rows = (
        db.query(User)
        .filter(
            User.id != current.id,
            User.is_active.is_(True),
            User.username.ilike(f"%{keyword}%"),
        )
        .order_by(User.username.asc())
        .limit(20)
        .all()
    )
    return [_social_user(user) for user in rows]


@router.get("/overview", response_model=SocialOverviewOut)
def social_overview(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    relations = (
        db.query(Friendship)
        .filter(
            or_(
                Friendship.requester_id == current.id,
                Friendship.addressee_id == current.id,
            )
        )
        .all()
    )

    accepted = [item for item in relations if item.status == "accepted"]
    incoming_rows = [
        item for item in relations if item.status == "pending" and item.addressee_id == current.id
    ]
    outgoing_rows = [
        item for item in relations if item.status == "pending" and item.requester_id == current.id
    ]

    friend_ids = [
        item.addressee_id if item.requester_id == current.id else item.requester_id
        for item in accepted
    ]
    user_ids = friend_ids + [item.requester_id for item in incoming_rows] + [
        item.addressee_id for item in outgoing_rows
    ]
    users = {
        user.id: user
        for user in db.query(User).filter(User.id.in_(set(user_ids))).all()
    } if user_ids else {}

    last_messages: dict[int, DirectMessage] = {}
    if friend_ids:
        messages = (
            db.query(DirectMessage)
            .filter(
                or_(
                    DirectMessage.sender_id == current.id,
                    DirectMessage.receiver_id == current.id,
                )
            )
            .order_by(DirectMessage.created_at.desc(), DirectMessage.id.desc())
            .all()
        )
        for message in messages:
            friend_id = (
                message.receiver_id
                if message.sender_id == current.id
                else message.sender_id
            )
            if friend_id in friend_ids and friend_id not in last_messages:
                last_messages[friend_id] = message

    unread_rows = (
        db.query(DirectMessage.sender_id, func.count(DirectMessage.id))
        .filter(
            DirectMessage.receiver_id == current.id,
            DirectMessage.is_read.is_(False),
        )
        .group_by(DirectMessage.sender_id)
        .all()
    )
    unread = {sender_id: int(count) for sender_id, count in unread_rows}

    friends = [
        FriendOut(
            **_social_user(users[friend_id]).model_dump(),
            last_message=last_messages[friend_id].content if friend_id in last_messages else None,
            last_message_at=last_messages[friend_id].created_at if friend_id in last_messages else None,
            unread_count=unread.get(friend_id, 0),
        )
        for friend_id in friend_ids
        if friend_id in users
    ]
    friends.sort(
        key=lambda item: item.last_message_at or datetime.min,
        reverse=True,
    )

    incoming = [
        _request_out(item, users[item.requester_id])
        for item in incoming_rows
        if item.requester_id in users
    ]
    outgoing = [
        _request_out(item, users[item.addressee_id])
        for item in outgoing_rows
        if item.addressee_id in users
    ]
    return SocialOverviewOut(
        friends=friends,
        incoming=incoming,
        outgoing=outgoing,
        unread_count=sum(item.unread_count for item in friends),
    )


@router.post(
    "/requests",
    response_model=FriendRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def send_friend_request(
    body: FriendRequestIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = (
        db.query(User)
        .filter(func.lower(User.username) == body.username.strip().lower())
        .first()
    )
    if target is None or not target.is_active:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.id == current.id:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    existing = _friendship_between(db, current.id, target.id)
    if existing is not None:
        if existing.status == "accepted":
            raise HTTPException(status_code=409, detail="你们已经是好友")
        if existing.requester_id == current.id:
            raise HTTPException(status_code=409, detail="好友申请已发送，请等待对方接受")
        raise HTTPException(status_code=409, detail="对方已向你发送申请，请直接接受")

    relation = Friendship(
        requester_id=current.id,
        addressee_id=target.id,
        status="pending",
    )
    db.add(relation)
    db.commit()
    db.refresh(relation)
    return _request_out(relation, target)


@router.post("/requests/{request_id}/accept")
def accept_friend_request(
    request_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    relation = db.get(Friendship, request_id)
    if relation is None:
        raise HTTPException(status_code=404, detail="好友申请不存在")
    if relation.addressee_id != current.id:
        raise HTTPException(status_code=403, detail="无权处理该申请")
    if relation.status != "pending":
        raise HTTPException(status_code=409, detail="该申请已处理")
    relation.status = "accepted"
    relation.updated_at = datetime.utcnow()
    db.commit()
    return {"success": True}


@router.delete("/requests/{request_id}")
def delete_friend_request(
    request_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    relation = db.get(Friendship, request_id)
    if relation is None:
        raise HTTPException(status_code=404, detail="好友申请不存在")
    if current.id not in (relation.requester_id, relation.addressee_id):
        raise HTTPException(status_code=403, detail="无权处理该申请")
    if relation.status != "pending":
        raise HTTPException(status_code=409, detail="该申请已处理")
    db.delete(relation)
    db.commit()
    return {"success": True}


@router.delete("/friends/{friend_id}")
def remove_friend(
    friend_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    relation = _friendship_between(db, current.id, friend_id)
    if relation is None or relation.status != "accepted":
        raise HTTPException(status_code=404, detail="好友关系不存在")
    db.query(DirectMessage).filter(
        or_(
            (DirectMessage.sender_id == current.id) & (DirectMessage.receiver_id == friend_id),
            (DirectMessage.sender_id == friend_id) & (DirectMessage.receiver_id == current.id),
        )
    ).delete(synchronize_session=False)
    db.delete(relation)
    db.commit()
    return {"success": True}


@router.get("/messages/{friend_id}", response_model=DirectMessageListOut)
def list_messages(
    friend_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    friend = _require_friend(db, current, friend_id)
    (
        db.query(DirectMessage)
        .filter(
            DirectMessage.sender_id == friend_id,
            DirectMessage.receiver_id == current.id,
            DirectMessage.is_read.is_(False),
        )
        .update({DirectMessage.is_read: True}, synchronize_session=False)
    )
    db.commit()
    query = db.query(DirectMessage).filter(
        or_(
            (DirectMessage.sender_id == current.id) & (DirectMessage.receiver_id == friend_id),
            (DirectMessage.sender_id == friend_id) & (DirectMessage.receiver_id == current.id),
        )
    )
    total = query.count()
    rows = query.order_by(DirectMessage.created_at.desc(), DirectMessage.id.desc()).limit(200).all()
    return DirectMessageListOut(
        friend=_social_user(friend),
        items=[
            DirectMessageOut(
                id=item.id,
                sender_id=item.sender_id,
                receiver_id=item.receiver_id,
                content=item.content,
                is_read=item.is_read,
                created_at=item.created_at,
                is_mine=item.sender_id == current.id,
            )
            for item in reversed(rows)
        ],
        total=total,
    )


@router.post(
    "/messages/{friend_id}",
    response_model=DirectMessageOut,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    friend_id: int,
    body: DirectMessageIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_friend(db, current, friend_id)
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="消息内容不能为空")
    message = DirectMessage(
        sender_id=current.id,
        receiver_id=friend_id,
        content=content,
    )
    db.add(message)
    relation = _friendship_between(db, current.id, friend_id)
    if relation is not None:
        relation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    return DirectMessageOut(
        id=message.id,
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        content=message.content,
        is_read=message.is_read,
        created_at=message.created_at,
        is_mine=True,
    )
