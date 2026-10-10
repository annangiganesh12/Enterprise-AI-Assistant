
from datetime import date

from app.database.database import SessionLocal
from app.models.company import(
    Department,
    Employee,
    LeaveRecord
)
from app.models.projects import Project
from app.models.customers import Sale,Customer

                # if we need the generated ID immediately i.e; it is a foreign key of some table then
                # we do db.flush() to immediately generate it otherwise no need to do flush

def seed_data():

    db = SessionLocal()

    try:

        # DEPARTMENTS

        engineering = Department(name="Engineering")
        ai = Department(name="AI")
        hr = Department(name="HR")
        sales_department = Department(name="Sales")

        db.add_all([
            engineering,
            ai,
            sales_department,
            hr
        ])

        db.flush()

        # EMPLOYEES

        employees = [
            Employee(
                name="Rahul",
                email="rahul@techcorp.com",
                joining_date=date(2024,5,10),
                department_id=engineering.id
            ),
            Employee(
                name="Priya",
                email="priya@techcorp.com",
                joining_date=date(2025, 2, 15),
                department_id=ai.id
            ),
            Employee(
                name="Arjun",
                email="arjun@techcorp.com",
                joining_date=date(2026, 1, 20),
                department_id=ai.id
            ),
            Employee(
                name="Sneha",
                email="sneha@techcorp.com",
                joining_date=date(2023, 8, 5),
                department_id=hr.id
            ),
            Employee(
                name="Vikram",
                email="vikram@techcorp.com",
                joining_date=date(2025, 7, 12),
                department_id=sales_department.id
            ),
            Employee(
                name="Ananya",
                email="ananya@techcorp.com",
                joining_date=date(2026, 3, 8),
                department_id=engineering.id
            ),
        ]

        db.add_all(employees)
        db.flush()           

        # LEAVE RECORDS

        leave_records = [
            LeaveRecord(
                employee_id=employees[0].id,
                leave_type="Annual",
                total_leaves=20,
                leaves_taken=8
            ),
            LeaveRecord(
                employee_id=employees[1].id,
                leave_type="Annual",
                total_leaves=20,
                leaves_taken=5
            ),
            LeaveRecord(
                employee_id=employees[2].id,
                leave_type="Annual",
                total_leaves=20,
                leaves_taken=3
            ),
            LeaveRecord(
                employee_id=employees[3].id,
                leave_type="Annual",
                total_leaves=24,
                leaves_taken=12
            ),
            LeaveRecord(
                employee_id=employees[4].id,
                leave_type="Annual",
                total_leaves=20,
                leaves_taken=10
            ),
            LeaveRecord(
                employee_id=employees[5].id,
                leave_type="Annual",
                total_leaves=20,
                leaves_taken=4
            ),
        ]

        db.add_all(leave_records)
        db.flush()

        # PROJECTS

        projects = [
            Project(
                name="Enterprise AI Assistant",
                description= "AI assistant using RAG,memory and agents",
                status="Active"
            ),
            Project(
                name="Customer Analytics Platform",
                description="Analytics platform for customer data",
                status="Active"
            ),
            Project(
                name="Legacy System Migration",
                description="Migration of legacy applications",
                status="Completed"
            ),
            Project(
                name="AI Document Processing",
                description="Automated document processing using AI",
                status="Planning"
            ),
        ]

        db.add_all(projects)
        db.flush()

        # CUSTOMERS

        customers = [
            Customer(
                name="Amit Sharma",
                email="amit@abcltd.com",
                company="ABC Ltd"
            ),
            Customer(
                name="Neha Reddy",
                email="neha@xyzpvt.com",
                company="XYZ Pvt Ltd"
            ),
            Customer(
                name="John Smith",
                email="john@acmecorp.com",
                company="Acme Corp"
            ),
            Customer(
                name="David Wilson",
                email="david@globaltech.com",
                company="GlobalTech"
            ),
            Customer(
                name="Meera Kapoor",
                email="meera@innovate.com",
                company="Innovate Solutions"
            ),
        ]

        db.add_all(customers)
        db.flush()

        # SALES

        sales = [
            Sale(
               customer_id=customers[0].id,
               amount=500000,
               sale_date=date(2026,1,15),
               product="Enterprise AI Assistant" 
            ),
            Sale(
                customer_id=customers[1].id,
                amount=250000,
                sale_date=date(2026, 2, 10),
                product="Analytics Platform"
            ),
            Sale(
                customer_id=customers[2].id,
                amount=750000,
                sale_date=date(2026, 3, 5),
                product="Enterprise License"
            ),
            Sale(
                customer_id=customers[3].id,
                amount=300000,
                sale_date=date(2026, 4, 20),
                product="Cloud API"
            ),
            Sale(
                customer_id=customers[4].id,
                amount=450000,
                sale_date=date(2026, 5, 12),
                product="Enterprise AI Assistant"
            ),
            Sale(
                customer_id=customers[0].id,
                amount=200000,
                sale_date=date(2026, 6, 18),
                product="Cloud API"
            ),
            Sale(
                customer_id=customers[2].id,
                amount=600000,
                sale_date=date(2026, 7, 8),
                product="Enterprise License"
            ),
            Sale(
                customer_id=customers[1].id,
                amount=350000,
                sale_date=date(2026, 8, 2),
                product="Analytics Platform"
            ),
        ]

        db.add_all(sales)
        db.flush()

        # commit everything

        db.commit()

        print("Company data inserted successfully!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
