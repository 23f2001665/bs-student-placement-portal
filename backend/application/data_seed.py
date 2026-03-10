from datetime import datetime
from faker import Faker

from flask import current_app as app

from .model import *
from .extensions import db, password_hasher
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
    
    branch_codes = {'CSE': "Computer Science and Engineering", 'ECE': "Electronics and Communication Engineering", 'ME': "Mechanical Engineering", 'CE': "Civil Engineering", 'EE': "Electrical Engineering", 'IT': "Information Technology", 'AERO': "Aerospace Engineering", 'BIO': "Biotechnology Engineering", 'CHEM': "Chemical Engineering", 'CIVIL': "Civil Engineering"}
    branches = []
    
    for prog in programmes:
        for branch_code, branch_name in branch_codes.items():
            branches.append(
                Branch(
                    prog_id=prog.id,
                    code=f"{prog.code}_{branch_code}",
                    name=f"{prog.name} in {branch_name}"
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
        
        
def reset_database():

    print("🧹 Clearing database safely...")

    db.session.query(Application).delete()

    db.session.query(PlacementDrive).delete()

    # Association table
    db.session.execute(
        db.text("DELETE FROM drive_eligibility_branches")
    )

    db.session.query(DriveEligibility).delete()

    db.session.query(Student).delete()
    db.session.query(Company).delete()

    db.session.query(User).filter(User.user_type != UserType.admin).delete()

    db.session.query(Branch).delete()
    db.session.query(Programme).delete()

    db.session.commit()

    print("✅ Database cleared")
    

import random
from datetime import datetime, timedelta, date, timezone

from faker import Faker
from werkzeug.security import generate_password_hash

from .extensions import db
from .model import (
    Programme, Branch, DriveEligibility,
    User, Student, Company,
    PlacementDrive, Application,

    UserType, Gender, WorkMode,
    DriveApprovalStatus, DriveStatus,
    ApplicationStatus
)

fake = Faker("en_IN")


# =====================================================
# CONFIG
# =====================================================

TOTAL_STUDENTS = 1000
TOTAL_COMPANIES = 25
TOTAL_DRIVES = 200
TOTAL_APPLICATIONS = 5000


PASSWORD = generate_password_hash("test@123")


# =====================================================
# MAIN SEEDER
# =====================================================

def seed_database_faker():

    print("🌱 Seeding database with Faker...")

    reset_database()        # removing everything except admin

    # -----------------------------------------------
    # PROGRAMMES AND BRANCHES
    # -----------------------------------------------
    seed_programme_branches()

    # -----------------------------------------------
    # DRIVE ELIGIBILITY
    # -----------------------------------------------
    eligibilities = []

    for i in range(10):

        min_cgpa = round(random.uniform(5.5, 8.0), 2)

        elig = DriveEligibility(
            description=f"CGPA >= {min_cgpa}",
            min_cgpa=min_cgpa,
            allowed_branches=random.sample(
                branches,
                random.randint(2, 5)
            )
        )

        eligibilities.append(elig)

    db.session.add_all(eligibilities)
    db.session.flush()


    # -----------------------------------------------
    # ADMIN
    # -----------------------------------------------
    admin = User(
        email="admin@test.com",
        password=PASSWORD,
        name="admin",
        user_type=UserType.admin
    )

    db.session.add(admin)
    db.session.flush()


    # -----------------------------------------------
    # STUDENTS
    # -----------------------------------------------
    students = []

    for i in range(TOTAL_STUDENTS):

        branch = random.choice(branches)
        programme = branch.programme

        admission_year = random.randint(2019, 2024)

        current_level = random.randint(
            1,
            programme.duration_years
        )

        dob = fake.date_between(
            start_date="-25y",
            end_date="-18y"
        )

        student = Student(
            email=f"student{i}@test.com",
            password=PASSWORD,
            name=fake.name(),

            user_type=UserType.student,

            dob=dob,
            gender=random.choice(list(Gender)),

            roll=f"ROLL{1000+i}",

            admission_year=admission_year,
            current_level=current_level,

            prog_id=programme.id,
            branch_id=branch.id,

            cgpa=round(random.uniform(4.5, 9.8), 2)
        )

        students.append(student)

    db.session.add_all(students)
    db.session.flush()


    # -----------------------------------------------
    # COMPANIES
    # -----------------------------------------------
    companies = []

    used_numbers = set()

    for i in range(TOTAL_COMPANIES):

        phone = None

        while not phone or phone in used_numbers:
            phone = fake.msisdn()[:10]

        used_numbers.add(phone)

        company = Company(
            email=f"company{i}@test.com",
            password=PASSWORD,
            name=fake.company(),

            user_type=UserType.company,

            is_approved=True,

            industry=fake.job()[:50],
            description=fake.text(200),

            website=fake.url(),
            location=fake.city(),

            contact_number=phone
        )

        companies.append(company)

    db.session.add_all(companies)
    db.session.flush()


    # -----------------------------------------------
    # PLACEMENT DRIVES
    # -----------------------------------------------
    drives = []

    now = datetime.now(timezone.utc)

    for i in range(TOTAL_DRIVES):

        company = random.choice(companies)
        eligibility = random.choice(eligibilities)

        start = fake.date_time_between(
            start_date="-30d",
            end_date="+15d",
            tzinfo=timezone.utc
        )

        end = start + timedelta(days=random.randint(7, 25))

        drive = PlacementDrive(
            company_id=company.id,

            approval_status=random.choice(list(DriveApprovalStatus)),
            status=random.choice(list(DriveStatus)),

            title=fake.job()[:60] + f" {i}",

            description=fake.text(300),

            work_mode=random.choice(list(WorkMode)),
            job_location=fake.city(),

            eligibility=eligibility.id,

            number_of_vacancies=random.randint(1, 20),

            opening=start,
            deadline=end
        )

        drives.append(drive)

    db.session.add_all(drives)
    db.session.flush()


    # -----------------------------------------------
    # APPLICATIONS
    # -----------------------------------------------
    applications = []

    used_pairs = set()

    for _ in range(TOTAL_APPLICATIONS):

        student = random.choice(students)
        drive = random.choice(drives)

        key = (student.id, drive.id)

        if key in used_pairs:
            continue

        used_pairs.add(key)

        applied = fake.date_time_between(
            start_date=drive.opening,
            end_date=min(drive.deadline, now),
            tzinfo=timezone.utc
        )

        app = Application(
            student_id=student.id,
            drive_id=drive.id,

            applied_on=applied,

            status=random.choice(list(ApplicationStatus)),

            resume_url=fake.url(),

            remarks=fake.sentence()
        )

        applications.append(app)

    db.session.add_all(applications)


    # -----------------------------------------------
    # FINAL COMMIT
    # -----------------------------------------------
    db.session.commit()

    print("✅ Faker seeding complete!")


