from database import SessionLocal
from models import Policy
from sqlalchemy.orm import joinedload
def get_policy_details(policy_id):
    db = SessionLocal()
    try:
        policy = (
            db.query(Policy)
            .options(
                joinedload(Policy.customer),
                joinedload(Policy.marketer),
                joinedload(Policy.insurance_type),
                joinedload(Policy.collections),
            )
            .filter(Policy.id == policy_id)
            .first()
        )
        if not policy:
            return None
        # پیدا کردن آخرین الحاقیه مربوط به همین بیمه‌نامه
        # تمام الحاقیه‌های یک بیمه‌نامه با issue_code مشترک هستند.
        latest_endorsement = (
            db.query(Policy)
            .filter(
                Policy.issue_code == policy.issue_code
            )
            .order_by(
                Policy.endorsement_number.desc()
            )
            .first()
        )
        return {
            "policy": policy,
            "collections": list(policy.collections),
            "latest_endorsement_number": (
                latest_endorsement.endorsement_number
                if latest_endorsement
                else policy.endorsement_number
            ),
        }
    finally:
        db.close()