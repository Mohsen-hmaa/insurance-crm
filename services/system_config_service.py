from database import SessionLocal
from models import SystemConfig
def get_current_agent():
    db = SessionLocal()
    try:
        config = (
            db.query(SystemConfig)
            .first()
        )
        if not config:
            return None
        return config.current_agent
    finally:
        db.close()
def update_current_agent(
    current_agent,
):
    current_agent = current_agent.strip()
    if not current_agent:
        raise ValueError(
            "نام نمایندگی نمی‌تواند خالی باشد."
        )
    db = SessionLocal()
    try:
        config = (
            db.query(SystemConfig)
            .first()
        )
        if not config:
            raise ValueError(
                "تنظیمات سیستم پیدا نشد."
            )
        config.current_agent = current_agent
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()