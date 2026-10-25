from models import InsuranceType
from database import SessionLocal
from sqlalchemy.orm import joinedload
def get_insurance_type_by_name(db,name):
    return (
        db.query(InsuranceType).filter(InsuranceType.name==name).first()
    )
def create_insurance_tree(db,data, parent=None, result=None):
    if result is None:
        result={}
    for item in data:
        insurance_type=InsuranceType(
            name=item["name"],
            parent=parent
        )
        db.add(insurance_type)
        result[item["name"]]=insurance_type
        if "children" in item:
            create_insurance_tree(
                db,
                item["children"],
                insurance_type,
                result
            )
    return result
def get_all_insurance_types(db):
    return db.query(InsuranceType).all()
def load_insurance_types():
    db=SessionLocal()
    try:
        return get_all_insurance_types(db)
    finally:
        db.close()
def get_root_insurance_types(db):
    return(
         db.query(InsuranceType)
        .options(
            joinedload(InsuranceType.children)
            .joinedload(InsuranceType.children)
            .joinedload(InsuranceType.children)
        )   
        .filter(
            InsuranceType.parent_id==None
        )
        .all()
    )
def load_root_insurance_types():
    db=SessionLocal()
    try:
        result= get_root_insurance_types(db)
        return result
    finally:
        db.close()
