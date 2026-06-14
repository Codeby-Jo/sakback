from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import Conversation, ConversationMessage, User
from security import get_current_user

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class SendMessageRequest(BaseModel):
    text: str
    msg_type: str = "text"  # text | system | image | video


@router.get("/")
def get_my_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all ACTIVE conversations the logged-in user is part of,
    with the other person's profile and the last message.
    """
    uid = current_user.id
    convos = db.query(Conversation).filter(
        ((Conversation.seeker_a_id == uid) | (Conversation.seeker_b_id == uid)),
        Conversation.status == "ACTIVE"
    ).order_by(Conversation.created_at.desc()).all()

    result = []
    for c in convos:
        other_id = c.seeker_b_id if c.seeker_a_id == uid else c.seeker_a_id
        other = db.query(User).filter(User.id == other_id).first()

        # last message
        last_msg = (
            db.query(ConversationMessage)
            .filter(ConversationMessage.conversation_id == c.conversation_id)
            .order_by(ConversationMessage.created_at.desc())
            .first()
        )

        result.append({
            "conversation_id": c.conversation_id,
            "status": c.status,
            "matchflow_step": c.matchflow_step,
            "photo_unlocked": c.photo_unlocked,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "other_user": {
                "id": other.id,
                "name": other.full_name,
                "initial": other.full_name[0].upper() if other.full_name else "?",
                "age": other.age,
                "city": other.city,
                "occupation": other.occupation,
            } if other else None,
            "last_message": {
                "text": last_msg.text,
                "time": last_msg.created_at.strftime("%I:%M %p") if last_msg.created_at else "",
                "is_mine": last_msg.sender_id == uid,
            } if last_msg else None,
        })

    return {"conversations": result}


@router.get("/{conversation_id}/messages")
def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all messages in a conversation.
    Only accessible if the user is a participant.
    """
    uid = current_user.id
    convo = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        ((Conversation.seeker_a_id == uid) | (Conversation.seeker_b_id == uid))
    ).first()

    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found or not accessible")

    msgs = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.asc())
        .all()
    )

    return {
        "conversation_id": conversation_id,
        "status": convo.status,
        "matchflow_step": convo.matchflow_step,
        "photo_unlocked": convo.photo_unlocked,
        "messages": [
            {
                "id": m.id,
                "text": m.text,
                "msg_type": m.msg_type,
                "sender": "me" if m.sender_id == uid else "them",
                "sender_id": m.sender_id,
                "time": m.created_at.strftime("%I:%M %p") if m.created_at else "",
            }
            for m in msgs
        ],
    }


@router.post("/{conversation_id}/messages")
def send_message(
    conversation_id: str,
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sends a message in a conversation.
    Both participants can send messages.
    """
    uid = current_user.id
    convo = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        ((Conversation.seeker_a_id == uid) | (Conversation.seeker_b_id == uid))
    ).first()

    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found or not accessible")

    if convo.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="This conversation is no longer active")

    msg = ConversationMessage(
        conversation_id=conversation_id,
        sender_id=uid,
        text=req.text,
        msg_type=req.msg_type,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {
        "id": msg.id,
        "text": msg.text,
        "msg_type": msg.msg_type,
        "sender": "me",
        "time": msg.created_at.strftime("%I:%M %p") if msg.created_at else "",
    }
