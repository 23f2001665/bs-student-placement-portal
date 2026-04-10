import os
import random
import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, time, date
from pathlib import Path

from faker import Faker # type: ignore
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, sessionmaker

try:
    from argon2 import PasswordHasher

    _password_hasher = PasswordHasher()

    def _hash_password(password: str) -> str:
        return _password_hasher.hash(password)
except Exception:
    from werkzeug.security import generate_password_hash

    def _hash_password(password: str) -> str:
        return generate_password_hash(password)


USER_TYPE_ADMIN = "admin"
USER_TYPE_STUDENT = "student"
USER_TYPE_COMPANY = "company"

GENDERS = ["m", "f", "o"]
BRANCH_KEYS = ["cse", "ece", "me", "ce", "ee", "ds", "it"]
INDUSTRY_KEYS = [
    "software",
    "finance",
    "healthcare",
    "education",
    "manufacturing",
    "retail",
    "energy",
    "transportation",
    "entertainment",
]
DRIVE_APPROVAL_KEYS = ["pending", "approved", "rejected"]
DRIVE_STATUS_KEYS = ["pending", "upcoming", "active", "closed", "cancelled"]
WORK_MODE_KEYS = ["onsite", "remote", "hybrid"]
APPLICATION_STATUS_KEYS = ["applied", "short_listed", "selected", "rejected"]


fake = Faker("en_IN")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED_ENV_PATH = PROJECT_ROOT / ".env"
if SEED_ENV_PATH.exists():
    from dotenv import load_dotenv

    load_dotenv(SEED_ENV_PATH)

JOB_PROFILES = [
    {
        "title": "Software Engineer",
        "team": "Core Platform",
        "skills": ["Python", "REST APIs", "SQL", "Git", "Unit Testing"],
        "responsibilities": [
            "Build and maintain backend services for high-traffic platforms",
            "Design and review API contracts with frontend and product teams",
            "Improve reliability through testing, observability, and tuning",
        ],
    },
    {
        "title": "Backend Developer",
        "team": "Payments Technology",
        "skills": ["Java", "Spring Boot", "PostgreSQL", "Redis", "Kafka"],
        "responsibilities": [
            "Implement fault-tolerant services for transaction processing",
            "Work on schema design and query optimization",
            "Collaborate with SRE to meet latency and uptime targets",
        ],
    },
    {
        "title": "Frontend Developer",
        "team": "Web Experience",
        "skills": ["Vue", "TypeScript", "Vite", "Accessibility", "Jest"],
        "responsibilities": [
            "Develop responsive interfaces for customer-facing workflows",
            "Translate designs into production-grade components",
            "Improve accessibility and cross-browser behavior",
        ],
    },
    {
        "title": "Data Analyst",
        "team": "Business Intelligence",
        "skills": ["SQL", "Python", "Power BI", "Statistics", "Data Modeling"],
        "responsibilities": [
            "Build dashboards that track product and business KPIs",
            "Perform exploratory analysis and present insights",
            "Partner with stakeholders to define and validate metrics",
        ],
    },
    {
        "title": "QA Engineer",
        "team": "Quality Engineering",
        "skills": ["Test Planning", "Automation", "Selenium", "API Testing", "CI/CD"],
        "responsibilities": [
            "Create automated regression suites for web and API layers",
            "Own release quality gates and defect triage workflows",
            "Improve testability of new features with developers",
        ],
    },
    {
        "title": "DevOps Engineer",
        "team": "Cloud Infrastructure",
        "skills": ["Linux", "Docker", "Kubernetes", "Terraform", "Monitoring"],
        "responsibilities": [
            "Manage CI/CD pipelines and deployment reliability",
            "Automate infrastructure provisioning and policy checks",
            "Enhance incident response readiness and observability coverage",
        ],
    },
    {
        "title": "Product Analyst",
        "team": "Growth Analytics",
        "skills": ["SQL", "A/B Testing", "Experimentation", "Excel", "Communication"],
        "responsibilities": [
            "Design and analyze experiments for funnel optimization",
            "Define metrics and reporting cadences for growth initiatives",
            "Translate analysis into roadmap recommendations",
        ],
    },
]

INTERVIEW_ROUNDS = [
    "Round 1: Online assessment on aptitude and coding fundamentals",
    "Round 2: Technical interview on problem solving and debugging",
    "Round 3: Hiring manager discussion on ownership and collaboration",
]


def _database_url() -> str:
    project_root = Path(__file__).resolve().parents[2]

    def _to_sqlite_url(path: Path) -> str:
        return f"sqlite:///{path.resolve()}"

    def _ensure_sqlite_parent(url: str):
        if not url.startswith("sqlite:///"):
            return
        raw_path = url[len("sqlite:///") :]
        if not raw_path:
            return
        db_path = Path(raw_path)
        if not db_path.is_absolute():
            db_path = project_root / db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)

    url = os.getenv("DATABASE_URI") or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URI or DATABASE_URL must be set in environment")

    if url.startswith("sqlite:///"):
        raw_path = url[len("sqlite:///") :]
        if raw_path and not raw_path.startswith("/"):
            # Match Flask's sqlite relative-path behavior (relative to instance path).
            resolved_url = _to_sqlite_url(project_root / "instance" / raw_path)
            _ensure_sqlite_parent(resolved_url)
            return resolved_url
        _ensure_sqlite_parent(url)
        return url

    return url


ENGINE = create_engine(_database_url(), future=True)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)
AutoBase = automap_base()
_MAPPED = None


def _required_tables_present() -> bool:
    try:
        tables = set(inspect(ENGINE).get_table_names())
    except Exception:
        return False
    return {"user", "student", "company", "drive", "application", "interview"}.issubset(tables)


def _ensure_schema_ready():
    if _required_tables_present():
        return

    from .models import db as app_db

    # Create schema directly on the seeder engine so table checks and automap
    # are always aligned with the actual target database URL.
    app_db.metadata.create_all(bind=ENGINE)

    if not _required_tables_present():
        raise RuntimeError("Database schema is not initialized for seeding")


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        _configure_sqlite_seed_session(session)
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _configure_sqlite_seed_session(session: Session):
    bind = session.get_bind()
    if bind is not None and bind.dialect.name == "sqlite":
        # SQLite rejects non-deterministic datetime CHECK expressions during bulk seed inserts.
        # This applies only to synthetic seeding sessions; runtime API validation remains unchanged.
        session.execute(text("PRAGMA ignore_check_constraints=ON"))


def _mapped_classes():
    global _MAPPED
    if _MAPPED is None:
        _ensure_schema_ready()
        AutoBase.prepare(autoload_with=ENGINE)
        _MAPPED = {
            "User": AutoBase.classes.user,
            "Student": AutoBase.classes.student,
            "Company": AutoBase.classes.company,
            "Drive": AutoBase.classes.drive,
            "Application": AutoBase.classes.application,
            "Interview": AutoBase.classes.interview,
        }
    return _MAPPED


def _random_name() -> str:
    return fake.name()


def _random_company_name() -> str:
    return fake.company()


def _random_website(name: str) -> str:
    slug = "".join(ch for ch in name.lower() if ch.isalnum()) or "company"
    return f"https://www.{slug[:24]}.com"


def _random_text(max_chars: int = 200) -> str:
    text = fake.text(max_nb_chars=max_chars)
    return text[:max_chars]


def _random_company_description(company_name: str, industry_key: str) -> str:
    del company_name
    industry = industry_key.replace("_", " ")
    templates = [
        "A fast-growing {industry} company building reliable digital products for enterprise and consumer users.",
        "An engineering-driven {industry} organization focused on quality, security, and customer outcomes.",
        "A {industry} business expanding teams across engineering, analytics, and operations.",
    ]
    return random.choice(templates).format(industry=industry)


def _build_drive_description(profile: dict) -> str:
    skills = ", ".join(profile["skills"])
    responsibilities = " ".join([f"- {item}" for item in profile["responsibilities"]])
    return (
        f"Role: {profile['title']} | Team: {profile['team']}\n"
        f"Required skills: {skills}.\n"
        f"Responsibilities: {responsibilities}\n"
        "Eligibility: Strong communication skills and ability to work in cross-functional teams."
    )


def _random_drive_state(start: datetime, end: datetime) -> tuple[str, str, bool]:
    del end
    approval = random.choices(DRIVE_APPROVAL_KEYS, weights=[20, 70, 10], k=1)[0]

    if approval == "pending":
        return approval, "pending", True

    if approval == "rejected":
        return approval, "cancelled", False

    now = datetime.now()
    if start > now:
        status = "upcoming"
    elif start + timedelta(days=20) < now:
        status = "closed"
    else:
        status = "active"

    return approval, status, True


def _random_interview_details() -> str:
    location = random.choice(
        [
            "Virtual (Microsoft Teams)",
            "Virtual (Google Meet)",
            "Onsite - Bengaluru Office",
            "Onsite - Chennai Office",
        ]
    )
    panel_size = random.choice([2, 3, 4])
    rounds = " | ".join(INTERVIEW_ROUNDS)
    return (
        f"Mode: {location}. Panel size: {panel_size}. "
        f"Please keep a valid photo ID and updated resume ready. {rounds}."
    )


def _derive_student_level_from_roll(roll: str, today: date | None = None) -> int:
    ref = today or date.today()
    intake_prefix = "".join(ch for ch in roll[:2] if ch.isdigit())
    if len(intake_prefix) != 2:
        return 1

    intake_year = 2000 + int(intake_prefix)
    level = ref.year - intake_year + (1 if ref.month >= 7 else 0)
    return max(1, min(level, 4))


def _random_industry_key() -> str:
    return random.choice(INDUSTRY_KEYS)


def _ensure_seed_student(session: Session):
    mapped = _mapped_classes()
    User = mapped["User"]
    Student = mapped["Student"]

    seed_email = "23f2001665@ds.study.iitm.ac.in"
    seed_roll = "23f2001665"

    existing = session.execute(
        select(User).where(User.email == seed_email)
    ).scalar_one_or_none()
    if existing and existing.user_type != USER_TYPE_STUDENT:
        raise RuntimeError(f"Existing user {seed_email} is not a student")

    conflicting_roll = session.execute(
        select(Student).where(Student.roll == seed_roll)
    ).scalar_one_or_none()
    if conflicting_roll and (not existing or conflicting_roll.id != existing.id):
        raise RuntimeError(f"Roll {seed_roll} is already used by another account")

    current_level = _derive_student_level_from_roll(seed_roll)

    if existing:
        existing.name = "Himanshu Rastogi"
        existing.password = _hash_password("Abcd@123")
        existing.is_active = True

        student = session.execute(
            select(Student).where(Student.id == existing.id)
        ).scalar_one_or_none()
        if student is None:
            student = Student(id=existing.id)
            session.add(student)

        student.gender = "m"
        student.roll = seed_roll
        student.branch = "ds"
        student.current_level = current_level
        student.cgpa = 8.5
        session.flush()
        return existing

    user = User(
        name="Himanshu Rastogi",
        email=seed_email,
        password=_hash_password("Abcd@123"),
        user_type=USER_TYPE_STUDENT,
        is_active=True,
    )
    session.add(user)
    session.flush()

    student = Student(
        id=user.id,
        gender="m",
        roll=seed_roll,
        branch="ds",
        current_level=current_level,
        cgpa=8.5,
    )
    session.add(student)
    session.flush()
    return user


def _ensure_seed_company(session: Session):
    mapped = _mapped_classes()
    User = mapped["User"]
    Company = mapped["Company"]

    seed_email = "tech@tech.com"
    existing = session.execute(
        select(User).where(User.email == seed_email)
    ).scalar_one_or_none()

    if existing and existing.user_type != USER_TYPE_COMPANY:
        raise RuntimeError(f"Existing user {seed_email} is not a company")

    if existing:
        existing.name = "Tech"
        existing.password = _hash_password("Abcd@123")
        existing.is_active = True

        company = session.execute(
            select(Company).where(Company.id == existing.id)
        ).scalar_one_or_none()
        if company is None:
            company = Company(id=existing.id)
            session.add(company)

        company.is_approved = True
        company.industry_type = "software"
        company.website = "https://tech.com"
        company.description = "Seed company account for testing"
        session.flush()
        return existing

    user = User(
        name="Tech",
        email=seed_email,
        password=_hash_password("Abcd@123"),
        user_type=USER_TYPE_COMPANY,
        is_active=True,
    )
    session.add(user)
    session.flush()

    company = Company(
        id=user.id,
        is_approved=True,
        industry_type="software",
        website="https://tech.com",
        description="Seed company account for testing",
    )
    session.add(company)
    session.flush()
    return user


def _ensure_admin_user(session: Session):
    mapped = _mapped_classes()
    User = mapped["User"]

    admin_email = str(os.getenv("ADMIN_EMAIL") or "").strip()
    admin_password = str(os.getenv("ADMIN_PASSWORD") or "")
    if not admin_email:
        raise RuntimeError("ADMIN_EMAIL is required in .env for data seeding")
    if not admin_password:
        raise RuntimeError("ADMIN_PASSWORD is required in .env for data seeding")
    existing_admin = session.execute(
        select(User).where(User.email == admin_email)
    ).scalar_one_or_none()
    if existing_admin:
        return existing_admin

    admin_user = User(
        name="Admin",
        email=admin_email,
        password=_hash_password(admin_password),
        user_type=USER_TYPE_ADMIN,
        is_active=True,
    )
    session.add(admin_user)
    session.flush()
    return admin_user


def reset_database(session: Session | None = None):
    mapped = _mapped_classes()
    Interview = mapped["Interview"]
    Application = mapped["Application"]
    Drive = mapped["Drive"]
    Student = mapped["Student"]
    Company = mapped["Company"]
    User = mapped["User"]

    def _run(s: Session):
        s.query(Interview).delete(synchronize_session=False)
        s.query(Application).delete(synchronize_session=False)
        s.query(Drive).delete(synchronize_session=False)
        s.query(Student).delete(synchronize_session=False)
        s.query(Company).delete(synchronize_session=False)
        s.query(User).filter(User.user_type != USER_TYPE_ADMIN).delete(synchronize_session=False)
        print("Database reset complete.")

    if session is not None:
        _run(session)
        return

    with session_scope() as s:
        _run(s)


def seed_students(number_of_students: int = 1000, session: Session | None = None):
    mapped = _mapped_classes()
    User = mapped["User"]
    Student = mapped["Student"]

    def _run(s: Session):
        _ensure_seed_student(s)
        default_password_hash = _hash_password("Abcd@123")
        student_rows = []

        for i in range(number_of_students):
            roll = f"S{i + 2:09d}"  # 10 chars, unique.
            user = User(
                    name=_random_name(),
                    email=f"{roll.lower()}@student.university.edu",
                    password=default_password_hash,
                    user_type=USER_TYPE_STUDENT,
                    is_active=True,
                )
            s.add(user)
            s.flush()

            student_rows.append(
                Student(
                    id=user.id,
                    gender=random.choice(GENDERS),
                    roll=roll,
                    branch=random.choice(BRANCH_KEYS),
                    current_level=random.randint(1, 4),
                    cgpa=round(random.uniform(5.0, 9.9), 2),
                )
            )

        s.add_all(student_rows)
        s.flush()
        print(f"Seeded {len(student_rows) + 1} students successfully.")

    if session is not None:
        _run(session)
        return

    with session_scope() as s:
        _run(s)


def clear_students(session: Session | None = None) -> int:
    mapped = _mapped_classes()
    Student = mapped["Student"]
    User = mapped["User"]

    def _run(s: Session) -> int:
        num_students = s.query(Student).delete(synchronize_session=False)
        num_users = s.query(User).filter(User.user_type == USER_TYPE_STUDENT).delete(synchronize_session=False)
        print(f"Deleted students={num_students}, users={num_users}")
        return num_students

    if session is not None:
        return _run(session)

    with session_scope() as s:
        return _run(s)


def seed_company(number_of_companies: int = 100, session: Session | None = None):
    mapped = _mapped_classes()
    User = mapped["User"]
    Company = mapped["Company"]

    def _run(s: Session):
        _ensure_seed_company(s)
        default_password_hash = _hash_password("Abcd@123")
        companies = []
        for i in range(number_of_companies):
            name = _random_company_name()
            slug = "".join(ch for ch in name.lower() if ch.isalnum())[:20] or f"company{i}"
            industry_key = _random_industry_key()
            user = User(
                    email=f"hr.{slug}{i}@corporate.university.edu",
                    password=default_password_hash,
                    user_type=USER_TYPE_COMPANY,
                    name=name[:63],
                    is_active=True,
                )
            s.add(user)
            s.flush()

            companies.append(
                Company(
                    id=user.id,
                    is_approved=True,
                    industry_type=industry_key,
                    website=_random_website(name)[:255],
                    description=_random_company_description(name, industry_key),
                )
            )

        s.add_all(companies)
        s.flush()
        print(f"Seeded {len(companies) + 1} companies successfully.")

    if session is not None:
        _run(session)
        return

    with session_scope() as s:
        _run(s)


def seed_drives(number_of_drives: int = 1000, session: Session | None = None):
    mapped = _mapped_classes()
    Company = mapped["Company"]
    Drive = mapped["Drive"]

    def _run(s: Session):
        companies = s.execute(select(Company)).scalars().all()
        if not companies:
            raise RuntimeError("No companies available. Seed companies first.")

        now = datetime.now()
        drives = []

        for i in range(number_of_drives):
            company = random.choice(companies)
            start = now + timedelta(days=random.randint(-10, 30))
            end = start + timedelta(days=random.randint(7, 45))
            profile = random.choice(JOB_PROFILES)
            approval_status, status, is_active = _random_drive_state(start, end)
            drives.append(
                Drive(
                    company_id=company.id,
                    is_active=is_active,
                    title=f"{profile['title']} - {profile['team']} ({i + 1})"[:255],
                    description=_build_drive_description(profile),
                    create_date=now,
                    start_date=start,
                    end_date=end,
                    approval_status=approval_status,
                    status=status,
                    work_mode=random.choice(WORK_MODE_KEYS),
                    min_cgpa=round(random.uniform(5.0, 9.5), 2),
                    allowed_branches=",".join(
                        random.sample(BRANCH_KEYS, random.randint(1, 4))
                    ),
                    max_applications=random.randint(20, 500),
                )
            )

        s.add_all(drives)
        s.flush()
        print(f"Seeded {len(drives)} drives successfully.")

    if session is not None:
        _run(session)
        return

    with session_scope() as s:
        _run(s)


def seed_applications(number_of_applications: int = 5000, session: Session | None = None):
    mapped = _mapped_classes()
    Student = mapped["Student"]
    Drive = mapped["Drive"]
    Application = mapped["Application"]
    Interview = mapped["Interview"]

    def _status_token(value) -> str:
        if hasattr(value, "name"):
            return str(value.name).lower()
        return str(value).lower()

    def _run(s: Session):
        students = s.execute(select(Student)).scalars().all()
        drives = s.execute(select(Drive)).scalars().all()

        if not students or not drives:
            raise RuntimeError("Students and drives are required before seeding applications.")

        applications = []
        interviews = []
        used_pairs = set()
        max_pairs = len(students) * len(drives)
        target = min(number_of_applications, max_pairs)

        while len(applications) < target:
            student = random.choice(students)
            drive = random.choice(drives)
            key = (student.id, drive.id)
            if key in used_pairs:
                continue
            used_pairs.add(key)
            status = random.choice(APPLICATION_STATUS_KEYS)
            app_date = datetime.now() - timedelta(days=random.randint(0, 180))
            applications.append(
                Application(
                    student_id=student.id,
                    drive_id=drive.id,
                    status=status,
                    application_date=app_date,
                )
            )

        s.add_all(applications)
        s.flush()

        for application in applications:
            if _status_token(application.status) not in {"short_listed", "selected"}:
                continue

            interview_dt = (application.application_date or datetime.now()) + timedelta(days=random.randint(2, 21))
            interviews.append(
                Interview(
                    application_id=application.id,
                    interview_date=interview_dt.date(),
                    interview_time=time(
                        hour=random.choice([10, 11, 14, 15, 16]),
                        minute=random.choice([0, 30]),
                    ),
                    details=_random_interview_details(),
                )
            )

        if interviews:
            s.add_all(interviews)
            s.flush()
        print(f"Seeded {len(applications)} applications successfully.")
        if interviews:
            print(f"Seeded {len(interviews)} interviews successfully.")

    if session is not None:
        _run(session)
        return

    with session_scope() as s:
        _run(s)


def seed_database_faker(
    total_students: int = 10,
    total_companies: int = 10,
    total_drives: int = 100,
    total_applications: int = 50,
):
    """Full schema-compatible seed pipeline without Flask app context."""
    with session_scope() as s:
        _configure_sqlite_seed_session(s)
        _ensure_admin_user(s)
        reset_database(s)
        _ensure_admin_user(s)
        seed_students(total_students, s)
        seed_company(total_companies, s)
        seed_drives(total_drives, s)
        seed_applications(total_applications, s)
    print("Seeding complete.")


def seed_core_entities_only():
    """Seed only admin + fixed student + fixed company accounts."""
    with session_scope() as s:
        _configure_sqlite_seed_session(s)
        _ensure_admin_user(s)
        _ensure_seed_student(s)
        _ensure_seed_company(s)
    print("Core entities seeded.")


def _parse_args():
    parser = argparse.ArgumentParser(description="Database seeding utility")
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Seed only admin, fixed student, and fixed company",
    )
    parser.add_argument("--students", type=int, default=10, help="Number of faker students")
    parser.add_argument("--companies", type=int, default=10, help="Number of faker companies")
    parser.add_argument("--drives", type=int, default=100, help="Number of faker drives")
    parser.add_argument("--applications", type=int, default=50, help="Number of faker applications")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.core_only:
        seed_core_entities_only()
    else:
        seed_database_faker(
            total_students=args.students,
            total_companies=args.companies,
            total_drives=args.drives,
            total_applications=args.applications,
        )
