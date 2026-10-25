import hashlib
import hmac
import os
from database import SessionLocal
from models import User
from sqlalchemy import func
ROLES = (
    "مدیر سیستم",
    "مدیر",
    "کاربر ارشد",
    "کاربر",
)
ROLE_LEVELS = {
    "کاربر": 1,
    "کاربر ارشد": 2,
    "مدیر": 3,
    "مدیر سیستم": 4,
}
def normalize_username(username):
    return (username or "").strip().lower()
def hash_password(password):
    salt = os.urandom(16).hex()
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        310000,
    ).hex()
    return f"{salt}${password_hash}"
def verify_password(password, stored_hash):
    try:
        salt, password_hash = stored_hash.split("$", 1)
    except ValueError:
        return False
    new_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        310000,
    ).hex()
    return hmac.compare_digest(
        new_hash,
        password_hash,
    )
def authenticate_user(username, password):
    username = normalize_username(username)
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(
                func.lower(User.username) == username,
                User.is_active.is_(True),
            )
            .first()
        )
        if not user:
            return None
        if not verify_password(
            password,
            user.password_hash,
        ):
            return None
        return {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
        }
    finally:
        db.close()
def can_manage_role(actor_role, target_role):
    actor_level = ROLE_LEVELS.get(
        actor_role,
        0,
    )
    target_level = ROLE_LEVELS.get(
        target_role,
        0,
    )
    return (
        actor_level > target_level
        and actor_level > 0
        and target_level > 0
    )
def get_manageable_roles(actor_role):
    actor_level = ROLE_LEVELS.get(
        actor_role,
        0,
    )
    return tuple(
        role
        for role in ROLES
        if ROLE_LEVELS.get(role, 0) < actor_level
    )
def load_users(actor_role):
    db = SessionLocal()
    try:
        query = db.query(User)
        if actor_role == "مدیر":
            query = query.filter(
                User.role != "مدیر سیستم"
            )
        elif actor_role not in (
            "مدیر سیستم",
            "مدیر",
        ):
            return []
        users = query.all()
        users.sort(
            key=lambda user: ROLE_LEVELS.get(
                user.role,
                0,
            ),
            reverse=True,
        )
        return users
    finally:
        db.close()
def get_user_by_id(user_id):
    db = SessionLocal()
    try:
        return (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )
    finally:
        db.close()
def create_user(
    full_name,
    username,
    password,
    role,
    actor_role,
):
    username = normalize_username(username)
    if not username:
        raise ValueError(
            "نام کاربری را وارد کنید."
        )
    db = SessionLocal()
    try:
        if role not in ROLES:
            raise ValueError(
                "نقش انتخاب‌شده معتبر نیست."
            )
        if not can_manage_role(
            actor_role,
            role,
        ):
            raise PermissionError(
                "شما اجازه ایجاد کاربری با این نقش را ندارید."
            )
        existing_user = (
            db.query(User)
            .filter(
                func.lower(User.username) == username
            )
            .first()
        )
        if existing_user:
            raise ValueError(
                "این نام کاربری قبلاً استفاده شده است."
            )
        user = User(
            full_name=full_name,
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def update_user(
    user_id,
    full_name,
    username,
    role,
    is_active,
    actor_role,
    actor_user_id,
    new_password=None,
):
    username = normalize_username(username)
    if not username:
        raise ValueError(
            "نام کاربری را وارد کنید."
        )
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("کاربر پیدا نشد.")
        if user.id == actor_user_id:
            raise PermissionError(
                "نمی‌توانید حساب کاربری خودتان را از این بخش ویرایش کنید."
            )
        if not can_manage_role(actor_role, user.role):
            raise PermissionError(
                "شما اجازه مدیریت این کاربر را ندارید."
            )
        if not can_manage_role(actor_role, role):
            raise PermissionError(
                "شما اجازه تعیین این نقش را ندارید."
            )
        existing_user = (
            db.query(User)
            .filter(
                func.lower(User.username) == username,
                User.id != user_id,
            )
            .first()
        )
        if existing_user:
            raise ValueError(
                "این نام کاربری قبلاً استفاده شده است."
            )
        user.username = username
        user.full_name = full_name
        user.role = role
        user.is_active = is_active
        # فقط اگر رمز جدید وارد شده باشد
        if new_password:
            user.password_hash = hash_password(new_password)
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def delete_user(
    user_id,
    actor_role,
    actor_user_id,
):
    db = SessionLocal()
    try:
        if actor_role != "مدیر سیستم":
            raise PermissionError(
                "فقط مدیر سیستم اجازه حذف کاربر را دارد."
            )
        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )
        if not user:
            raise ValueError(
                "کاربر پیدا نشد."
            )
        if user.id == actor_user_id:
            raise PermissionError(
                "نمی‌توانید حساب کاربری خودتان را حذف کنید."
            )
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def toggle_user_active(
    user_id,
    actor_role,
    actor_user_id,
):
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )
        if not user:
            raise ValueError(
                "کاربر پیدا نشد."
            )
        if user.id == actor_user_id:
            raise PermissionError(
                "نمی‌توانید حساب کاربری خودتان را غیرفعال کنید."
            )
        if not can_manage_role(
            actor_role,
            user.role,
        ):
            raise PermissionError(
                "شما اجازه مدیریت این کاربر را ندارید."
            )
        user.is_active = not user.is_active
        db.commit()
        db.refresh(user)
        return user.is_active
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def change_user_password(
    user_id,
    new_password,
    actor_role,
    actor_user_id,
):
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )
        if not user:
            raise ValueError(
                "کاربر پیدا نشد."
            )
        if user.id != actor_user_id:
            if not can_manage_role(
                actor_role,
                user.role,
            ):
                raise PermissionError(
                    "شما اجازه تغییر رمز این کاربر را ندارید."
                )
        user.password_hash = hash_password(
            new_password
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def change_password(
    user_id,
    current_password,
    new_password,
    confirm_password,
):
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(
                User.id == user_id
            )
            .first()
        )
        if not user:
            raise ValueError(
                "کاربر پیدا نشد."
            )
        if not current_password:
            raise ValueError(
                "رمز عبور فعلی را وارد کنید."
            )
        if not new_password:
            raise ValueError(
                "رمز عبور جدید را وارد کنید."
            )
        if not confirm_password:
            raise ValueError(
                "تکرار رمز عبور جدید را وارد کنید."
            )
        if not verify_password(
            current_password,
            user.password_hash,
        ):
            raise ValueError(
                "رمز عبور فعلی صحیح نیست."
            )
        if new_password != confirm_password:
            raise ValueError(
                "رمز عبور جدید و تکرار آن یکسان نیستند."
            )
        if current_password == new_password:
            raise ValueError(
                "رمز عبور جدید باید با رمز عبور فعلی متفاوت باشد."
            )
        user.password_hash = hash_password(
            new_password
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()