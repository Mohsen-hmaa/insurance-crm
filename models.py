from database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Boolean,
    Float,
    Numeric,
)
from sqlalchemy.orm import relationship
class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    family = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    customer_type = Column(String)
    national_id = Column(String, unique=True)
    customer_code = Column(String, unique=True)
    is_active = Column(Boolean, default=True)
    policies = relationship("Policy", back_populates="customer")
    def __repr__(self):
        return f"<Customer id={self.id} name={self.name} {self.family}>"
class InsuranceCompany(Base):
    __tablename__ = "insurance_companies"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    is_active = Column(Boolean, default=True)
    policies = relationship("Policy", back_populates="company")
    def __repr__(self):
        return f"<InsuranceCompany id={self.id} name={self.name}>"
class InsuranceType(Base):
    __tablename__ = "insurance_types"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    display_name = Column(String)
    parent_id = Column(Integer, ForeignKey("insurance_types.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    has_mortgage = Column(Boolean, default=False)
    policies = relationship("Policy", back_populates="insurance_type")
    parent = relationship("InsuranceType", remote_side=[id], back_populates="children")
    children = relationship("InsuranceType", back_populates="parent")
    excel_mappings = relationship(
        "InsuranceTypeMapping",
        back_populates="insurance_type",
        cascade="all, delete-orphan",
    )
    commissions = relationship(
        "InsuranceTypeCommission",
        back_populates="insurance_type",
        cascade="all, delete-orphan",
    )
    def __repr__(self):
        return f"<InsuranceType id={self.id} name={self.display_name}>"
class InsuranceTypeMapping(Base):
    __tablename__ = "insurance_type_mappings"
    id = Column(Integer, primary_key=True)
    excel_name = Column(String, unique=True, nullable=True)
    insurance_type_id = Column(
        Integer, ForeignKey("insurance_types.id"), nullable=False, index=True
    )
    insurance_type = relationship("InsuranceType", back_populates="excel_mappings")
    def __repr__(self):
        return f"<InsuranceTypeMapping id={self.id} excel_name={self.excel_name}>"
class Policy(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True)
    policy_number = Column(String, nullable=False)
    customer_id = Column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    insurance_company_id = Column(
        Integer, ForeignKey("insurance_companies.id"), nullable=True, index=True
    )
    insurance_type_id = Column(
        Integer, ForeignKey("insurance_types.id"), nullable=False, index=True
    )
    start_date = Column(Date, nullable=True, index=True)
    end_date = Column(Date, nullable=True, index=True)
    # مبلغ ریالی بدون اعشار؛ در صورت نیاز به اعشار از Numeric استفاده شود
    premium = Column(Integer, nullable=False)
    mortgage_premium = Column(Integer, nullable=False, default=0)
    referrer = Column(String, nullable=True)
    marketer_id = Column(
        Integer, ForeignKey("marketers.id"), nullable=True, index=True
    )
    referrer_type = Column(String, nullable=False, default="none")
    issuer = Column(String, nullable=True)
    referrer_work_unit = Column(String, nullable=True)
    is_mortgage = Column(Boolean, default=False)
    issue_date = Column(Date, nullable=False, index=True)
    fund = Column(Integer, nullable=False, default=0)
    endorsement_number = Column(Integer, nullable=False, default=0)
    issue_code = Column(String, nullable=False, index=True)
    computer_code = Column(String, nullable=False, unique=True, index=True)
    customer = relationship("Customer", back_populates="policies")
    marketer = relationship("Marketer", back_populates="policies")
    company = relationship("InsuranceCompany", back_populates="policies")
    insurance_type = relationship("InsuranceType", back_populates="policies")
    collections = relationship("Collection", back_populates="policy")
    def __repr__(self):
        return f"<Policy id={self.id} number={self.policy_number} issue_code={self.issue_code}>"
class Marketer(Base):
    __tablename__ = "marketers"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    # درصدها با Numeric تا خطای گرد کردن Float در محاسبات مالی رخ ندهد
    third_party_commission = Column(Numeric(5, 2), nullable=False)
    other_commission = Column(Numeric(5, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    policies = relationship("Policy", back_populates="marketer")
    def __repr__(self):
        return f"<Marketer id={self.id} name={self.name}>"
class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True)
    policy_id = Column(
        Integer, ForeignKey("policies.id"), nullable=True, index=True
    )
    settlement_operation_code = Column(String, nullable=False, index=True)
    # توجه: این فیلد یک ForeignKey واقعی نیست، فقط یک رشته‌ی متنی است.
    # منطق اصلی برنامه باید بر پایه‌ی policy_id (رابطه‌ی واقعی) باشد؛
    # این فیلد را فقط برای نمایش/آرشیو در نظر بگیرید مگر اینکه policy_id
    # همیشه قابل پر شدن نباشد.
    policy_computer_code = Column(String, nullable=False, index=True)
    settlement_amount = Column(Integer, nullable=True)
    due_date = Column(Date, nullable=True, index=True)
    collection_date = Column(Date, nullable=True, index=True)
    receipt_type = Column(String, nullable=True)
    debt_type = Column(String, nullable=True)
    due_computer_code = Column(String, nullable=True, index=True)
    receipt_document_number = Column(String, nullable=True, index=True)
    policy = relationship("Policy", back_populates="collections")
    def __repr__(self):
        return f"<Collection id={self.id} policy_id={self.policy_id}>"
class MarketerCommissionRule(Base):
    __tablename__ = "marketer_commission_rules"
    id = Column(Integer, primary_key=True)
    marketer_id = Column(
        Integer, ForeignKey("marketers.id"), nullable=False, index=True
    )
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=True, index=True)
    customer_id = Column(
        Integer, ForeignKey("customers.id"), nullable=True, index=True
    )
    insurance_type_id = Column(
        Integer, ForeignKey("insurance_types.id"), nullable=True, index=True
    )
    is_mortgage = Column(Boolean, nullable=True)
    commission_percent = Column(Numeric(5, 2), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    marketer = relationship("Marketer")
    policy = relationship("Policy")
    customer = relationship("Customer")
    insurance_type = relationship("InsuranceType")
    def __repr__(self):
        return f"<MarketerCommissionRule id={self.id} marketer_id={self.marketer_id}>"
class InsuranceTypeCommission(Base):
    __tablename__ = "insurance_type_commissions"
    id = Column(Integer, primary_key=True)
    insurance_type_id = Column(
        Integer, ForeignKey("insurance_types.id"), nullable=False, index=True
    )
    effective_date = Column(Date, nullable=True, index=True)
    normal_commission = Column(Numeric(5, 2), nullable=True)
    mortgage_commission = Column(Numeric(5, 2), nullable=True)
    issuance_percent = Column(Numeric(5, 2), nullable=False)
    insurance_type = relationship("InsuranceType", back_populates="commissions")
    def __repr__(self):
        return f"<InsuranceTypeCommission id={self.id} insurance_type_id={self.insurance_type_id}>"
class CommissionConfig(Base):
    __tablename__ = "commission_configs"
    id = Column(Integer, primary_key=True)
    effective_date = Column(Date, nullable=False, unique=True)
    first_step_commission = Column(Integer, nullable=False)
    vat = Column(Numeric(5, 2), nullable=False)
    def __repr__(self):
        return f"<CommissionConfig id={self.id} effective_date={self.effective_date}>"
class SystemConfig(Base):
    __tablename__ = "system_configs"
    id = Column(Integer, primary_key=True)
    current_agent = Column(String, nullable=False)
    def __repr__(self):
        return f"<SystemConfig id={self.id} current_agent={self.current_agent}>"
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String(30), nullable=False, default="کاربر")
    is_active = Column(Boolean, default=True)
    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"
