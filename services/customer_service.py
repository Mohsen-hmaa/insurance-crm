from models import Customer
from database import SessionLocal
def create_customer(db,data):
    customer=Customer(
        name=data["name"],
        family=data["family"],
        phone=data["phone"],
        customer_type=data["customer_type"],
        national_id=data["national_id"],
        customer_code=data["customer_code"]
    )
    db.add(customer)
    db.flush()
    return customer
def register_customer(data):
    db=SessionLocal()
    try:
        customer=create_customer(db,data)
        db.commit()
        db.refresh(customer)
        return customer
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
def update_customer(customer_id, data):
    db = SessionLocal()
    try:
        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )
        if not customer:
            raise ValueError("بیمه‌گذار مورد نظر پیدا نشد")
        customer.name = data["name"]
        customer.family = data["family"]
        customer.phone = data["phone"]
        customer.customer_type = data["customer_type"]
        customer.national_id = data["national_id"]
        customer.customer_code = data["customer_code"]
        db.commit()
        db.refresh(customer)
        return customer
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def get_all_customers(db):
    return db.query(Customer).all()    
def load_customers():
    db=SessionLocal()
    try:
        return get_all_customers(db)
    finally:
        db.close()
def get_customer_by_id(customer_id):
    db=SessionLocal()
    try:
        return(
            db.query(Customer)
                .filter(Customer.id==customer_id)
               .first()
        )
    finally:
        db.close()
def toggle_customer_active(customer_id):
    db = SessionLocal()
    try:
        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )
        if not customer:
            raise ValueError("بیمه‌گذار مورد نظر پیدا نشد")
        customer.is_active = not customer.is_active
        db.commit()
        db.refresh(customer)
        return customer
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()