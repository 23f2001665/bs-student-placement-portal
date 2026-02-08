from datetime import datetime
from faker import Faker

from flask import current_app as app

from .model import *
from .extension import db, password_hasher
from .model import Gender



fake = Faker()

def seed_programme_branches():

    programmes = [
        Programme(code="BTECH", name="Bachelor of Technology", duration_years=4),
        Programme(code="MTECH", name="Master of Technology", duration_years=2),
        Programme(code="MBA", name="Master of Business Administration", duration_years=2),
        Programme(code="PHD", name="Doctor of Philosophy", duration_years=5),
        Programme(code="DIPLOMA", name="Diploma Programme", duration_years=3),
        Programme(code="BARCH", name="Bachelor of Architecture", duration_years=5),
        Programme(code="MSC", name="Master of Science", duration_years=2),
        Programme(code="MA", name="Master of Arts", duration_years=2),
        Programme(code="BBA", name="Bachelor of Business Administration", duration_years=3),
        Programme(code="LLB", name="Bachelor of Laws", duration_years=3),
        Programme(code="LLM", name="Master of Laws", duration_years=2),
        Programme(code="BPHARMA", name="Bachelor of Pharmacy", duration_years=4),
        Programme(code="MPHARMA", name="Master of Pharmacy", duration_years=2),
        Programme(code="BSC", name="Bachelor of Science", duration_years=3),
        Programme(code="BA", name="Bachelor of Arts", duration_years=3),
        Programme(code="MFA", name="Master of Fine Arts", duration_years=2),
        Programme(code="BCOM", name="Bachelor of Commerce", duration_years=3),
        Programme(code="MCOM", name="Master of Commerce", duration_years=2),
        Programme(code="BDS", name="Bachelor of Dental Surgery", duration_years=5),
        Programme(code="MD", name="Doctor of Medicine", duration_years=3),
        Programme(code="MS", name="Master of Surgery", duration_years=3),
        Programme(code="BVSC", name="Bachelor of Veterinary Science", duration_years=5),
        Programme(code="MVSC", name="Master of Veterinary Science", duration_years=2),
        Programme(code="BPHIL", name="Bachelor of Philosophy", duration_years=3),
        Programme(code="MPHIL", name="Master of Philosophy", duration_years=2),
        Programme(code="BCA", name="Bachelor of Computer Applications", duration_years=3),
        Programme(code="MCA", name="Master of Computer Applications", duration_years=2),
        Programme(code="BFA", name="Bachelor of Fine Arts", duration_years=4),
        Programme(code="BTTM", name="Bachelor of Tourism and Travel Management", duration_years=3),
        Programme(code="MJMC", name="Master of Journalism and Mass Communication", duration_years=2),
        Programme(code="BHM", name="Bachelor of Hotel Management", duration_years=4),
        Programme(code="MHM", name="Master of Hotel Management", duration_years=2),
        Programme(code="BID", name="Bachelor of Industrial Design", duration_years=4),
        Programme(code="MID", name="Master of Industrial Design", duration_years=2),
        Programme(code="BAS", name="Bachelor of Applied Science", duration_years=3),
        Programme(code="MAS", name="Master of Applied Science", duration_years=2),
        Programme(code="BPT", name="Bachelor of Physiotherapy", duration_years=4),
        Programme(code="MPT", name="Master of Physiotherapy", duration_years=2),
        Programme(code="MBBS", name="Bachelor of Medicine and Bachelor of Surgery", duration_years=5),
        Programme(code="BSCN", name="Bachelor of Science in Nursing", duration_years=4),
        Programme(code="MSCN", name="Master of Science in Nursing", duration_years=2)
    ]

    try:
        db.session.add_all(programmes)
        db.session.commit()
        print("Seeded programmes successfully.")
    except Exception as e:
        db.session.rollback()
        app.logger.critical(f"Error seeding programmes: {e}")
    
    branches = [
        Branch(
            prog_id=db.session.query(Programme).filter_by(code="BTECH").first().id,
            code="CSE",
            name="Computer Science and Engineering" 
        )]
    
    for prog in programmes:
        for i in range(1, 6):
            branches.append(
                Branch(
                    prog_id=prog.id,
                    code=f"{prog.code}_BR{i}",
                    name=f"{prog.name} Branch {i}"
                )
            )
    try:
        db.session.add_all(branches)
        db.session.commit()
        print("Seeded branches successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding branches: {e}")

    
def clear_programme_branches():
    try:
        num_branches_deleted = db.session.query(Branch).delete()
        num_programmes_deleted = db.session.query(Programme).delete()
        db.session.commit()
        print(f"Deleted {num_branches_deleted} branches and {num_programmes_deleted} programmes.")
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing programmes and branches: {e}")

def seed_students(number_of_students=1000):
    students = [
        Student(
            name="Himanshu Rastogi",
            email="himanshu.rastogi@example.com",
            password=password_hasher.hash("pass"),
            dob=datetime(2000, 5, 15),
            gender=Gender.m,
            roll="2023BT1001",
            prog_id=103,
            branch_id=1,
            admission_year=2023,
            current_level=3
        )
    ]

    # Replace manual entries with generated dataset
    fake_students = []

    programmes = db.session.query(Programme).filter(Programme.is_active == 1).all()
    branches = db.session.query(Branch).filter(Branch.is_active == 1).all()

    branches_by_prog = {}
    for b in branches:
        branches_by_prog.setdefault(b.prog_id, []).append(b)

    if not programmes or not branches:
        raise RuntimeError("No active programmes/branches found. Seed programmes/branches before seeding students.")

    default_password_hash = password_hasher.hash("password123")
    used_rolls = set()
    current_year = datetime.now().year

    for i in range(number_of_students):
        prog = fake.random_element(programmes)
        candidate_branches = branches_by_prog.get(prog.id) or branches
        branch = fake.random_element(candidate_branches)

        gender = fake.random_element([Gender.m, Gender.f])
        name = fake.name_male() if gender == Gender.m else fake.name_female()
        email = fake.unique.email()

        admission_year = fake.random_int(min=2018, max=current_year)
        duration = int(getattr(prog, "duration_years", 4) or 4)
        max_level = max(1, min(duration, current_year - admission_year + 1))
        current_level = fake.random_int(min=1, max=max_level)

        min_age = max(17, 17 + (admission_year - 2018))
        dob_date = fake.date_of_birth(minimum_age=min_age, maximum_age=30)
        dob = datetime.combine(dob_date, datetime.min.time())

        prog_code = "".join(ch for ch in (getattr(prog, "code", "PRG") or "PRG") if ch.isalnum()).upper()[:6] or "PRG"
        roll = f"{admission_year}{prog_code}{i + 1:04d}"
        while roll in used_rolls:
            roll = f"{admission_year}{prog_code}{fake.random_int(min=1, max=9999):04d}"
        used_rolls.add(roll)

        fake_students.append(
            Student(
                name=name,
                email=email,
                password=default_password_hash,
                dob=dob,
                gender=gender,
                roll=roll,
                prog_id=prog.id,
                branch_id=branch.id,
                admission_year=admission_year,
                current_level=current_level,
            )
        )
    try:
        db.session.add_all(fake_students)
        db.session.commit()
        print("Seeded students successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding students: {e}")
    

def clear_students():
    try:
        num_deleted = db.session.query(Student).delete()
        num2_deleted = db.session.query(User).filter(User.user_type == UserType.student).delete()
        if num_deleted != num2_deleted:
            print(f"Warning: Mismatch in deleted counts: Students={num_deleted}, Users={num2_deleted}")
            return (f"Warning: Mismatch in deleted counts: Students={num_deleted}, Users={num2_deleted}")

        db.session.commit()
        print(f"Deleted {num_deleted} students.")
        return num_deleted
    
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing students: {e}")
        return 0

def seed_company(number_of_companies=100):
    companies = []
    company = Company(
        email="contact@reliabletechsolutions.com",
        password=password_hasher.hash("abcd1234"),
        user_type=UserType.company,
        name="Reliable Tech Solutions",
        industry="Information Technology",
        description="A leading provider of innovative tech solutions for businesses worldwide.",
        website="https://www.reliabletechsolutions.com",
        location="1234 Innovation Drive, Tech City, TC 56789",
        contact_number="1234567890"
    )

    companies.append(company)

    for i in range(number_of_companies - 1):
        name = fake.company()
        email = fake.unique.company_email()
        industry = fake.random_element(elements=("Information Technology", "Finance", "Healthcare", "Education", "Manufacturing", "Retail", "Consulting", "Real Estate", "Transportation", "Energy"))
        description = fake.text(max_nb_chars=200)
        website = fake.url()
        location = fake.address().replace("\n", ", ")
        contact_number = fake.phone_number().replace("-", "").replace(" ", "")[:10]

        company = Company(
            email=email,
            password=password_hasher.hash("abcd1234"),
            user_type=UserType.company,
            name=name,
            industry=industry,
            description=description,
            website=website,
            location=location,
            contact_number=contact_number
        )
        companies.append(company)
    try:
        db.session.add_all(companies)
        db.session.commit()
        print("Seeded company successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding company: {e}")    