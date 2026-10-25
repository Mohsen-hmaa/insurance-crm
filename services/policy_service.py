from models import Policy,InsuranceType
from database import SessionLocal
from services.date_service import convert_shamsi_to_date
from sqlalchemy.orm import joinedload
def create_policy(db, data):
    policy = Policy(
        policy_number=data["policy_number"],
        customer_id=data["customer_id"],
        insurance_type_id=data["insurance_type_id"],
        premium=int(
            data["premium"].replace(",", "").strip()
        ),
        start_date=(
            convert_shamsi_to_date(data["start_date"])
            if data["start_date"]
            else None
        ),
        end_date=(
            convert_shamsi_to_date(data["end_date"])
            if data["end_date"]
            else None
        ),
        issue_date=convert_shamsi_to_date(
            data["issue_date"]
        ),
        fund=int(
            data["fund"]
        ),
        endorsement_number=int(
            data["endorsement_number"]
        ),
        marketer_id=data["marketer_id"],
        referrer=data["referrer"],
        referrer_type=data["referrer_type"],
        is_mortgage=data["is_mortgage"]
    )
    db.add(policy)
    return policy
def register_policy(data):
        db=SessionLocal()
        try:
            policy=create_policy(db,data)
            db.commit()
            db.refresh(policy)
            return policy
        except Exception:
               db.rollback()
               raise
        finally:
               db.close()
def update_policy(policy_id, data):
    db = SessionLocal()
    try:
        policy = (
            db.query(Policy)
            .filter(Policy.id == policy_id)
            .first()
        )
        if not policy:
            raise ValueError("بیمه نامه پیدا نشد")
        policy.marketer_id = data["marketer_id"]
        policy.referrer = data["referrer"]
        policy.referrer_type = data["referrer_type"]
        policy.is_mortgage = data["is_mortgage"]
        db.commit()
        db.refresh(policy)
        return policy
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def delete_policy(policy_id):
    db=SessionLocal()
    try:
        policy=(
            db.query(Policy)
            .filter(Policy.id==policy_id)
            .first()
        )
        if not policy:
            return False
        db.delete(policy)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def load_policies():
    db=SessionLocal()
    try:
        return (
              db.query(Policy)
              .options(
                   joinedload(Policy.customer),
                   joinedload(Policy.insurance_type),
                   joinedload(Policy.marketer),
                    )
              .all()  
        )      
    finally:
        db.close()
def get_policy_by_id(policy_id):
    db = SessionLocal()
    try:
        return (
            db.query(Policy)
            .options(
                joinedload(Policy.customer),
                joinedload(Policy.insurance_type),
                joinedload(Policy.marketer),
                joinedload(Policy.insurance_type)
                .joinedload(InsuranceType.parent)
                .joinedload(InsuranceType.parent)
                .joinedload(InsuranceType.parent)
                .joinedload(InsuranceType.parent)
                .joinedload(InsuranceType.parent)
            )
            .filter(Policy.id == policy_id)
            .first()
        )
    finally:
        db.close()
