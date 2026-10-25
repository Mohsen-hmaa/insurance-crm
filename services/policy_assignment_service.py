from database import SessionLocal
from models import Policy
from sqlalchemy.orm import joinedload
def get_customers_from_new_policies(new_policies):
    customers = {}
    for policy in new_policies:
        customer = policy.customer
        if customer and customer.id not in customers:
            customers[customer.id] = customer
    return list(customers.values())
def get_customer_policies(customer_id):
    db = SessionLocal()
    try:
        return (
            db.query(Policy)
            .options(
                joinedload(Policy.customer),
                joinedload(Policy.marketer),
            )
            .filter(Policy.customer_id == customer_id)
            .all()
        )
    finally:
        db.close()
def get_latest_marketer(policies):
    policies_with_marketer = [
        policy
        for policy in policies
        if policy.marketer is not None
    ]
    if not policies_with_marketer:
        return None
    return max(
        policies_with_marketer,
        key=lambda policy: policy.issue_date
    ).marketer
def get_latest_referrer(policies):
    policies_with_referrer = [
        policy
        for policy in policies
        if (
            policy.referrer is not None
            and policy.referrer != "مرکز کد 110001"
            and policy.referrer != "شعبه آپادانا کد 110002"
        )
    ]
    if not policies_with_referrer:
        return None
    return max(
        policies_with_referrer,
        key=lambda policy: policy.issue_date
    ).referrer
def get_policies_without_marketer(policies):
    return [
        policy
        for policy in policies
        if policy.marketer is None
    ]
def get_policies_without_referrer(policies):
    return [
        policy
        for policy in policies
        if policy.referrer is None
    ]
def get_marketer_assignment_candidates(policies):
    latest_marketer = get_latest_marketer(policies)
    if latest_marketer is None:
        return []
    policies_without_marketer = get_policies_without_marketer(
        policies
    )
    return [
        {
            "policy": policy,
            "suggested_marketer": latest_marketer
        }
        for policy in policies_without_marketer
    ]
def get_referrer_assignment_candidates(policies):
    latest_referrer = get_latest_referrer(policies)
    policies_without_referrer = get_policies_without_referrer(
        policies
    )
    if latest_referrer is None:
        return []
    return [
        {
            "policy": policy,
            "suggested_referrer": latest_referrer
        }
        for policy in policies_without_referrer
    ]
def get_assignment_candidates(policies):
    customers = {}
    for policy in policies:
        if policy.customer_id not in customers:
            customers[policy.customer_id] = []
        customers[policy.customer_id].append(policy)
    result = []
    for customer_id, customer_policies in customers.items():
        marketer_candidates = get_marketer_assignment_candidates(
            customer_policies
        )
        referrer_candidates = get_referrer_assignment_candidates(
            customer_policies
        )
        if marketer_candidates or referrer_candidates:
            result.append({
                "customer_id": customer_id,
                "policies": customer_policies,
                "marketer_candidates": marketer_candidates,
                "referrer_candidates": referrer_candidates
            })
    return result
def get_all_policies_for_assignment(db):
    return (
        db.query(Policy)
        .options(
            joinedload(Policy.customer),
            joinedload(Policy.marketer),
        )
        .all()
    )
def assign_marketer(policies, marketer):
    db = SessionLocal()
    try:
        policy_ids = [policy.id for policy in policies]
        if not policy_ids:
            return
        policies_db = (
            db.query(Policy)
            .filter(Policy.id.in_(policy_ids))
            .all()
        )
        for policy_db in policies_db:
            policy_db.marketer_id = marketer.id
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def assign_referrer(policies, referrer):
    db = SessionLocal()
    try:
        policy_ids = [policy.id for policy in policies]
        if not policy_ids:
            return
        policies_db = (
            db.query(Policy)
            .filter(Policy.id.in_(policy_ids))
            .all()
        )
        for policy_db in policies_db:
            policy_db.referrer = referrer
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def get_assignment_candidates_for_new_policies(new_policies):
    new_policy_ids = [
        policy.id
        for policy in new_policies
    ]
    if not new_policy_ids:
        return []
    db = SessionLocal()
    try:
        new_policies_db = (
            db.query(Policy)
            .filter(Policy.id.in_(new_policy_ids))
            .all()
        )
        result = []
        customer_ids = {
            policy.customer_id
            for policy in new_policies_db
        }
        for customer_id in customer_ids:
            customer_policies = get_customer_policies(
                customer_id
            )
            candidates = get_assignment_candidates(
                customer_policies
            )
            result.extend(candidates)
        return result
    finally:
        db.close()
def get_all_assignment_candidates():
    db = SessionLocal()
    try:
        policies = get_all_policies_for_assignment(db)
        return get_assignment_candidates(policies)
    finally:
        db.close()
