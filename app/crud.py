import random
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from . import models
from .seed_data import TAG_LABELS


def image_src(image_filename: str) -> str:
    return f"/static/images/{image_filename}"


def serialize_design(design: models.NailDesign):
    return {
        "id": design.id,
        "title": design.title,
        "description": design.description,
        "image_filename": design.image_filename,
        "image_src": image_src(design.image_filename),
        "tags": design.tag_list,
        "tag_labels": [TAG_LABELS.get(tag, tag.title()) for tag in design.tag_list],
    }


def get_or_create_user(db: Session, telegram_id: str, username: str | None = None, first_name: str | None = None):
    user = db.query(models.User).filter(models.User.telegram_id == str(telegram_id)).first()
    if user:
        if username and user.username != username:
            user.username = username
        if first_name and user.first_name != first_name:
            user.first_name = first_name
        db.commit()
        db.refresh(user)
        return user

    user = models.User(telegram_id=str(telegram_id), username=username, first_name=first_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_public_alias(user: models.User) -> str:
    if user.username:
        return user.username.lstrip("@")
    return f"user{user.telegram_id}"


def get_user_by_alias(db: Session, alias: str):
    needle = alias.strip().lstrip("@")
    if not needle:
        return None

    user = db.query(models.User).filter(func.lower(models.User.username) == needle.lower()).first()
    if user:
        return user

    if needle.startswith("user") and needle[4:].isdigit():
        user = db.query(models.User).filter(models.User.telegram_id == needle[4:]).first()
        if user:
            return user

    if needle.isdigit():
        user = db.query(models.User).filter(models.User.telegram_id == needle).first()
        if user:
            return user

    user = db.query(models.User).filter(func.lower(models.User.first_name) == needle.lower()).first()
    return user


def get_all_catalog_designs(db: Session):
    return db.query(models.NailDesign).order_by(models.NailDesign.id.asc()).all()


def get_random_design(db: Session):
    ids = [row[0] for row in db.query(models.NailDesign.id).all()]
    if not ids:
        return None
    return db.query(models.NailDesign).filter(models.NailDesign.id == random.choice(ids)).first()


def get_designs_by_tag(db: Session, tag: str):
    needle = tag.strip().lower()
    return [
        design
        for design in db.query(models.NailDesign).order_by(models.NailDesign.id.asc()).all()
        if needle in [t.lower() for t in design.tag_list]
    ]


def save_design_for_user(db: Session, telegram_id: str, design_id: int, username: str | None = None, first_name: str | None = None):
    user = get_or_create_user(db, telegram_id, username, first_name)
    existing = (
        db.query(models.SavedDesign)
        .filter(models.SavedDesign.user_id == user.id, models.SavedDesign.design_id == design_id)
        .first()
    )
    if existing:
        return False

    db.add(models.SavedDesign(user_id=user.id, design_id=design_id))
    db.commit()
    return True


def remove_saved_design_for_user(db: Session, telegram_id: str, design_id: int):
    row = (
        db.query(models.SavedDesign)
        .join(models.User)
        .filter(models.User.telegram_id == str(telegram_id), models.SavedDesign.design_id == design_id)
        .first()
    )
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def get_saved_designs_for_user(db: Session, telegram_id: str, tag: str | None = None):
    rows = (
        db.query(models.SavedDesign)
        .join(models.User)
        .join(models.NailDesign)
        .options(joinedload(models.SavedDesign.design))
        .filter(models.User.telegram_id == str(telegram_id))
        .all()
    )
    designs = [row.design for row in rows]
    if tag:
        needle = tag.strip().lower()
        designs = [design for design in designs if needle in [t.lower() for t in design.tag_list]]
    return designs


def get_saved_tags_for_user(db: Session, telegram_id: str):
    tags = []
    seen = set()
    for design in get_saved_designs_for_user(db, telegram_id):
        for tag in design.tag_list:
            if tag not in seen:
                tags.append(tag)
                seen.add(tag)
    return tags
