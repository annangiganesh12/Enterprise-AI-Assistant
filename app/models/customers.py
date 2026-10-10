

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base

class Customer(Base):

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    email = Column(String,nullable=False,unique=True)
    company = Column(String)

    sales = relationship(
        "Sale",
        back_populates="customer"
    )

class Sale(Base):


    __tablename__ = "sales"

    id = Column(Integer,primary_key=True,index=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    amount = Column(Float, nullable=False)
    sale_date = Column(Date,nullable=False)
    product = Column(String, nullable=False)

    customer = relationship(
        "Customer",
        back_populates="sales"
    )