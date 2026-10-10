

from datetime  import date

from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base

class Department(Base):

    __tablename__ = "departments"

    id = Column(Integer,primary_key=True,index=True)
    name = Column(String,nullable=False,unique=True)

    employees = relationship(
        "Employee",
        back_populates="department"
    )

class Employee(Base):

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True,index=True)
    name = Column(String,nullable=False)
    email = Column(String,nullable=False,unique=True)
    joining_date = Column(Date,nullable=False)

    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False
    )

    department = relationship(
        "Department",
        back_populates="employees"
    )

    leave_records = relationship(
        "LeaveRecord",
        back_populates="employee"
    )


class LeaveRecord(Base):

    __tablename__ = "leave_records"

    id = Column(Integer,primary_key=True,index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False
    )

    leave_type = Column(String,nullable=False)
    total_leaves = Column(Integer,nullable=False)
    leaves_taken = Column(Integer,nullable=False,default=0)

    employee = relationship(
        "Employee",
        back_populates="leave_records"
    )