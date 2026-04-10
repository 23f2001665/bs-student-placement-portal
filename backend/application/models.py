from ..extensions import *
from datetime import datetime
from sqlalchemy import CheckConstraint, case, func, literal
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum

#################################################################
# Enums
#################################################################


class UserType(Enum):
    admin="admin"
    student="student"
    company="company"

class Gender(Enum):
    m="male"
    f="female"
    o="other"

class DriveApprovalStatus(Enum):
    pending="Pending"
    approved="Approved"
    rejected="Rejected"
    
class DriveStatus(Enum):
    upcoming="Upcoming"
    active="Active"
    closed="Closed"
    cancelled="Cancelled"
    pending="Pending"

class WorkMode(Enum):
    onsite = "Onsite"
    remote = "Remote"
    hybrid = "Hybrid"

class ApplicationStatus(Enum):
    applied="Applied"
    short_listed="ShortListed"
    selected="Selected"
    rejected="Rejected"

class Branches(Enum):
    cse = "Computer Science and Engineering"
    ece = "Electronics and Communication Engineering"
    me = "Mechanical Engineering"
    ce = "Civil Engineering"
    ee = "Electrical Engineering"
    ds = "Data Science"
    it = "Information Technology"
    
class IndustryType(Enum):
    software = "Software"
    finance = "Finance"
    healthcare = "Healthcare"
    education = "Education"
    manufacturing = "Manufacturing"
    retail = "Retail"
    energy = "Energy"
    transportation = "Transportation"
    entertainment = "Entertainment"

class User(db.Model):
    __tablename__ = "user"

    # authentication fields
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(255), nullable=False, unique=True)
    password=db.Column(db.String(255), nullable=False)          # argon hashed
    is_active=db.Column(db.Boolean, nullable=False, default=True)
    user_type=db.Column(db.Enum(UserType, native_enum=False), nullable=False)
    name=db.Column(db.String(63), nullable=False)
    
    # dumping format
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "is_active": self.is_active,
            "user_type": self.user_type.value,
            "name": self.name
        }

    # table constraints
    __table_args__ = (
        CheckConstraint("length(trim(email)) > 0", name="user_email_not_blank"),
        CheckConstraint("length(trim(name)) > 0", name="user_name_not_blank"),
        db.Index("idx_user_type_active", "user_type", "is_active"),
    )

    # mapper args
    __mapper_args__ = {
        "polymorphic_on":user_type,
        "polymorphic_identity": UserType.admin
    }

class Student(User):
    __tablename__ = "student"

    id=db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    gender=db.Column(db.Enum(Gender, native_enum=False), nullable=True)

    # college specific fields
    roll = db.Column(db.String(10), unique=True, nullable=False, index=True)
    branch = db.Column(db.Enum(Branches, native_enum=False), nullable=False, index=True)
    current_level = db.Column(db.Integer, nullable=False, index=True)   # year of study
    cgpa = db.Column(db.Float, nullable=True)
    resume_path = db.Column(db.String(255), nullable=True)

    # relationships
    applications=db.relationship("Application", back_populates="student", cascade="all, delete-orphan", lazy="selectin")

    # dumping format
    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "gender": self.gender.value if self.gender else None,
            "roll": self.roll,
            "branch": self.branch.value if self.branch else None,
            "current_level": self.current_level,
            "cgpa": self.cgpa,
            "resume_path": self.resume_path
        })
        return base_dict

    __table_args__ = (
            CheckConstraint("length(trim(roll)) > 0", name="student_roll_not_blank"),
            CheckConstraint('current_level >= 1', name="student_current_level_positive"),
            CheckConstraint('cgpa >= 0.0 AND cgpa <= 10.0', name="student_cgpa_valid")
        )

    __mapper_args__ = {
        "polymorphic_identity": UserType.student
    }

class Company(User):
    __tablename__ = "company"

    id=db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    is_approved=db.Column(db.Boolean, nullable=False, default=False, index=True)
    industry_type=db.Column(db.Enum(IndustryType, native_enum=False), nullable=False, index=True)
    website=db.Column(db.String(255), nullable=False)
    description=db.Column(db.Text, nullable=True)

    # relationships
    drives=db.relationship("Drive", back_populates="company", cascade="all, delete-orphan", lazy="selectin")
    applications = db.relationship(
    "Application",
    primaryjoin="Company.id == Drive.company_id",
    secondary="drive",
    secondaryjoin="Drive.id == Application.drive_id",
    viewonly=True,
    lazy="selectin"
    )

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "is_approved": self.is_approved,
            "industry_type": self.industry_type.value if self.industry_type else None,
            "website": self.website,
            "description": self.description
        })
        return base_dict

    __mapper_args__ = {
        "polymorphic_identity": UserType.company
    }

    __table_args__ = (
        CheckConstraint("length(trim(website)) > 0", name="company_website_not_blank"),
    )


class Drive(db.Model):
    __tablename__ = "drive"

    id=db.Column(db.Integer, primary_key=True)
    company_id=db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    is_active=db.Column(db.Boolean, nullable=False, default=True, index=True)
    title=db.Column(db.String(255), nullable=False)
    description=db.Column(db.Text, nullable=True)
    create_date=db.Column(db.DateTime, nullable=False, index=True)
    start_date=db.Column(db.DateTime, nullable=False, index=True)
    end_date=db.Column(db.DateTime, nullable=False, index=True)
    approval_status=db.Column(db.Enum(DriveApprovalStatus, native_enum=False), nullable=False, default=DriveApprovalStatus.pending, index=True)
    status=db.Column(db.Enum(DriveStatus, native_enum=False),nullable=False, index=True)
    work_mode=db.Column(db.Enum(WorkMode, native_enum=False), nullable=False, index=True)
    min_cgpa=db.Column(db.Float, nullable=True)
    allowed_branches=db.Column(db.String(255), nullable=True)  # comma separated branches
    max_applications=db.Column(db.Integer, nullable=True)

    # relationships
    company=db.relationship("Company", back_populates="drives", lazy="joined")
    applications=db.relationship("Application", back_populates="drive", cascade="all, delete-orphan", lazy="selectin")
                                 
    # property to get allowed branches as list
    @property
    def allowed_branches_list(self):
        if self.allowed_branches:
            valid = {b.name for b in Branches}
            return [b.strip() for b in self.allowed_branches.split(",") if b.strip() in valid]
        return []

    @staticmethod
    def _derive_effective_status(approval_status, persisted_status, is_active, start_date, end_date, now):
        del persisted_status

        if not is_active:
            return DriveStatus.cancelled

        if approval_status != DriveApprovalStatus.approved:
            return DriveStatus.pending

        if start_date and now < start_date:
            return DriveStatus.upcoming

        if end_date and now > end_date:
            return DriveStatus.closed

        return DriveStatus.active

    @hybrid_property
    def effective_status(self):
        ref_dt = self.start_date or self.end_date
        if ref_dt is not None and ref_dt.tzinfo is not None and ref_dt.tzinfo.utcoffset(ref_dt) is not None:
            now = datetime.now(ref_dt.tzinfo)
        else:
            now = datetime.now()

        return Drive._derive_effective_status(
            self.approval_status,
            self.status,
            self.is_active,
            self.start_date,
            self.end_date,
            now,
        )

    @effective_status.expression
    def effective_status(cls):
        current_local_dt = func.datetime("now", "localtime")
        return case(
            (
                cls.is_active.is_(False),
                literal(DriveStatus.cancelled.name),
            ),
            (
                cls.approval_status != DriveApprovalStatus.approved,
                literal(DriveStatus.pending.name),
            ),
            (
                (cls.approval_status == DriveApprovalStatus.approved)
                & (current_local_dt < cls.start_date),
                literal(DriveStatus.upcoming.name),
            ),
            (
                (cls.approval_status == DriveApprovalStatus.approved)
                & (current_local_dt > cls.end_date),
                literal(DriveStatus.closed.name),
            ),
            (
                cls.approval_status == DriveApprovalStatus.approved,
                literal(DriveStatus.active.name),
            ),
            else_=literal(DriveStatus.pending.name),
        )
    
    # dumping format

    def to_dict(self):
        effective_status = self.effective_status
        return {
            "id": self.id,
            "company_id": self.company_id,
            "is_active": self.is_active,
            "title": self.title,
            "description": self.description,
            "create_date": self.create_date.isoformat() if self.create_date else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "approval_status": self.approval_status.value if self.approval_status else None,
            "status": effective_status.value if effective_status else None,
            "work_mode": self.work_mode.value if self.work_mode else None,
            "min_cgpa": self.min_cgpa,
            "allowed_branches": self.allowed_branches_list,
            "max_applications": self.max_applications
        }

    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="drive_title_not_blank"),
        CheckConstraint('end_date >= start_date', name="drive_date_order_valid"),
        CheckConstraint('start_date >= create_date', name="drive_start_not_before_create"),
        CheckConstraint(
            "approval_status != 'pending' OR is_active = 1",
            name="drive_pending_must_be_active",
        ),
        CheckConstraint(
            "approval_status != 'rejected' OR is_active = 0",
            name="drive_rejected_must_be_inactive",
        ),
        CheckConstraint('min_cgpa >= 0.0 AND min_cgpa <= 10.0', name="drive_min_cgpa_valid"),
        CheckConstraint('max_applications > 0', name="drive_max_applications_positive"),
        db.Index("idx_drive_company_active", "company_id", "is_active")
    )


class Application(db.Model):
    __tablename__ = "application"

    id=db.Column(db.Integer, primary_key=True)
    student_id=db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    drive_id=db.Column(db.Integer, db.ForeignKey("drive.id"), nullable=False, index=True)
    application_date=db.Column(db.DateTime, nullable=False, index=True, server_default=db.func.now())
    status=db.Column(db.Enum(ApplicationStatus, native_enum=False), nullable=False, default=ApplicationStatus.applied, index=True)
    resume_note=db.Column(db.Text, nullable=True)
    resume_link=db.Column(db.String(255), nullable=True)

    # SQLite CHECK constraints cannot query Drive; cross-table drive validity is enforced in apply_to_drive.
    __table_args__ = (
    db.UniqueConstraint('student_id', 'drive_id', name='uq_student_drive'),
    db.Index('idx_student_drive', 'student_id', 'drive_id')
    )

    # relationships
    student=db.relationship("Student", lazy="joined", back_populates="applications")
    drive=db.relationship("Drive", back_populates="applications", lazy="joined")
    company=db.relationship("Company", secondary="drive", back_populates="applications", viewonly=True, lazy="joined", uselist=False)
    interview=db.relationship("Interview", back_populates="application", uselist=False, cascade="all, delete-orphan", lazy="joined")

    # dumping format
    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "drive_id": self.drive_id,
            "application_date": self.application_date.isoformat() if self.application_date else None,
            "status": self.status.value if self.status else None,
            "resume_note": self.resume_note,
            "resume_link": self.resume_link,
            "interview": self.interview.to_dict() if self.interview else None,
        }


class Interview(db.Model):
    __tablename__ = "interview"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=False, unique=True, index=True)
    interview_date = db.Column(db.Date, nullable=False, index=True)
    interview_time = db.Column(db.Time, nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    application = db.relationship("Application", back_populates="interview", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "interview_date": self.interview_date.isoformat() if self.interview_date else None,
            "interview_time": self.interview_time.isoformat() if self.interview_time else None,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    __table_args__ = (
        CheckConstraint(
            "details IS NULL OR length(trim(details)) > 0",
            name='interview_details_not_blank',
        ),
    )
