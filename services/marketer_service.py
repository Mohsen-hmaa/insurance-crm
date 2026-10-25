from models import Marketer,MarketerCommissionRule
from database import SessionLocal
from sqlalchemy.orm import joinedload
def create_marketer(db,data):
    marketer=Marketer(
        name=data["name"],
        third_party_commission=data["third_party_commission"],
        other_commission=data["other_commission"]
    )
    db.add(marketer)
    return marketer
def register_marketer(data):
    db=SessionLocal()
    try:
        marketer=create_marketer(db,data)
        db.commit()
        db.refresh(marketer)
        return marketer
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def get_all_marketers(db):
    return (
        db.query(Marketer)
        .filter(Marketer.is_active==True)
        .all()
    )        
def load_marketers():
    db=SessionLocal()
    try:
        return get_all_marketers(db)
    finally:
        db.close()
def update_marketer(marketer_id, data):
    db = SessionLocal()
    try:
        marketer = db.query(Marketer).filter(
            Marketer.id == marketer_id
        ).first()
        if not marketer:
            raise ValueError("بازاریاب پیدا نشد")
        marketer.name = data["name"]
        marketer.third_party_commission = (
            data["third_party_commission"]
        )
        marketer.other_commission = (
            data["other_commission"]
        )
        db.commit()
        db.refresh(marketer)
        return marketer
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def get_marketer_by_id(marketer_id):
    db = SessionLocal()
    try:
        return db.query(Marketer).filter(
            Marketer.id == marketer_id
        ).first()
    finally:
        db.close()
def create_commission_rule(data):
    db = SessionLocal()
    try:
        rule = MarketerCommissionRule(
            marketer_id=data["marketer_id"],
            policy_id=data.get("policy_id"),
            customer_id=data.get("customer_id"),
            insurance_type_id=data.get("insurance_type_id"),
            is_mortgage=data.get("is_mortgage"),
            commission_percent=data["commission_percent"],
            start_date=data.get("start_date"),
            end_date=data.get("end_date")
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def get_commission_rules(marketer_id):
    db = SessionLocal()
    try:
        return (
            db.query(MarketerCommissionRule)
            .options(
                joinedload(
                    MarketerCommissionRule.customer
                ),
                joinedload(
                    MarketerCommissionRule.insurance_type
                ),
                joinedload(
                    MarketerCommissionRule.policy
                )
            )
            .filter(
                MarketerCommissionRule.marketer_id == marketer_id
            )
            .all()
        )
    finally:
        db.close()
def has_commission_rules(marketer_id):
    db = SessionLocal()
    try:
        return (
            db.query(MarketerCommissionRule.id)
            .filter(
                MarketerCommissionRule.marketer_id == marketer_id
            )
            .first()
            is not None
        )
    finally:
        db.close()
def delete_commission_rule(rule_id):
    db = SessionLocal()
    try:
        rule = db.query(MarketerCommissionRule).filter(
            MarketerCommissionRule.id == rule_id
        ).first()
        if not rule:
            raise ValueError("قانون کمیسیون پیدا نشد")
        db.delete(rule)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def find_best_commission_rule(
    marketer_id,
    policy
):
    db = SessionLocal()
    try:
        rules = (
            db.query(MarketerCommissionRule)
            .filter(
                MarketerCommissionRule.marketer_id == marketer_id,
                MarketerCommissionRule.is_active == True
            )
            .all()
        )
        matching_rules = []
        for rule in rules:
            # قانون مخصوص یک بیمه‌نامه
            if rule.policy_id is not None:
                if rule.policy_id != policy.id:
                    continue
                return rule
            condition_count = 0
            # شرط مشتری
            if rule.customer_id is not None:
                if rule.customer_id != policy.customer_id:
                    continue
                condition_count += 1
            # شرط نوع بیمه
            if rule.insurance_type_id is not None:
                if rule.insurance_type_id != policy.insurance_type_id:
                    continue
                condition_count += 1
            # شرط مرهون بودن
            if rule.is_mortgage is not None:
                if rule.is_mortgage != policy.is_mortgage:
                    continue
                condition_count += 1
            # شرط تاریخ
            if rule.start_date is not None:
                if policy.issue_date < rule.start_date:
                    continue
            if rule.end_date is not None:
                if policy.issue_date > rule.end_date:
                    continue
            matching_rules.append(
                (
                    condition_count,
                    rule
                )
            )
        if not matching_rules:
            return None
        matching_rules.sort(
            key=lambda item: item[0],
            reverse=True
        )
        highest_count = matching_rules[0][0]
        best_rules = [
            rule
            for count, rule in matching_rules
            if count == highest_count
        ]
        if len(best_rules) > 1:
            raise ValueError(
                f"تداخل قوانین کارمزد برای بیمه‌نامه "
                f"{policy.id} وجود دارد"
            )
        return best_rules[0]
    finally:
        db.close()