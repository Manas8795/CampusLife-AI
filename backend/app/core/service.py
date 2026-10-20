import hashlib
import datetime
from sqlalchemy.orm import Session
from backend.app.core.models import User, Profile, UserPreference, Notification
from backend.app.core.schemas import UserRegister, ProfileUpdate, UserPreferenceUpdate, NotificationCreate

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

class CoreService:
    @staticmethod
    def register_user(db: Session, data: UserRegister) -> User:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise ValueError("User with this email already exists")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        profile = Profile(
            user_id=user.id,
            college=data.college or "",
            major=data.major or "",
            phone_number=data.phone_number or ""
        )
        prefs = UserPreference(user_id=user.id)
        welcome_notification = Notification(
            user_id=user.id,
            title="Welcome to CampusLife AI!",
            message="Your unified student co-pilot is ready to assist you across academics, wellness, finances, and travel.",
            category="SYSTEM",
            priority="LOW"
        )
        db.add_all([profile, prefs, welcome_notification])
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        return user

    @staticmethod
    def update_profile(db: Session, user_id: int, data: ProfileUpdate) -> Profile:
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            profile = Profile(user_id=user_id)
            db.add(profile)
        for key, value in data.dict(exclude_unset=True).items():
            setattr(profile, key, value)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_preferences(db: Session, user_id: int) -> UserPreference:
        prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not prefs:
            prefs = UserPreference(user_id=user_id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        return prefs

    @staticmethod
    def update_preferences(db: Session, user_id: int, data: UserPreferenceUpdate) -> UserPreference:
        prefs = CoreService.get_preferences(db, user_id)
        for key, value in data.dict(exclude_unset=True).items():
            if value is not None:
                setattr(prefs, key, value)
        db.commit()
        db.refresh(prefs)
        return prefs

    @staticmethod
    def create_notification(db: Session, user_id: int, notif: NotificationCreate) -> Notification:
        item = Notification(
            user_id=user_id,
            title=notif.title,
            message=notif.message,
            category=notif.category,
            priority=notif.priority
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_notifications(db: Session, user_id: int, limit: int = 20) -> list[Notification]:
        return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def mark_notification_read(db: Session, user_id: int, notif_id: int) -> bool:
        notif = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == user_id).first()
        if notif:
            notif.is_read = True
            db.commit()
            return True
        return False

    @staticmethod
    def mark_all_notifications_read(db: Session, user_id: int) -> int:
        count = db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).update({"is_read": True})
        db.commit()
        return count
