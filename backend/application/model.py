
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy import event
from .extensions import db
from datetime import datetime, timezone
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

class WorkMode(Enum):
    onsite = "Onsite"
    remote = "Remote"
    hybrid = "Hybrid"

class ApplicationStatus(Enum):
    applied="Applied"
    short_listed="ShortListed"
    selected="Selected"
    rejected="Rejected"


################################################################
# SOMEWHAT STATIC DATA CLASSES
################################################################

class Programme(db.Model):
    """
    Docstring for Programme
    """
    __tablename__ = "programme"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)
    code = db.Column(db.String(7), nullable=False, unique=True)
    duration_years = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # relationships
    branches = db.relationship("Branch", back_populates="programme", lazy="selectin", uselist=True)
    students = db.relationship("Student", lazy="selectin", uselist=True, back_populates="programme")

    __table_args__ = (
        CheckConstraint('duration_years > 0', name="programme_duration_positive"),
    )

    def __repr__(self):
        return f"Programme id={self.id} code={self.code} name={self.name}"

    __str__ = __repr__

class Branch(db.Model):
    """
    Docstring for Branch
    """
    __tablename__ = "branch"

    id = db.Column(db.Integer, primary_key=True)
    prog_id = db.Column(db.Integer, db.ForeignKey("programme.id"), nullable=False)
    code = db.Column(db.String(15), nullable=False, unique=True)        # global branch codes
    name = db.Column(db.String(63), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # relationships
    programme = db.relationship("Programme", back_populates="branches", lazy="joined", uselist=False)
    students = db.relationship("Student", lazy="selectin", uselist=True, back_populates="branch")

    # Table Constraints
    # branch_naming at event-listener and also check at application level

    def __repr__(self):
        return f"<Branch id={self.id} code={self.code} name={self.name} prog_id={self.prog_id}>"

    __str__ = __repr__


class DriveEligibility(db.Model):
    """
    Docstring for DriveEligibility
    """
    __tablename__ = "drive_eligibility"

    # drive eligibility fields
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    min_cgpa = db.Column(db.Float, nullable=False)
    allowed_branches = db.relationship("Branch", secondary="drive_eligibility_branches", lazy="selectin", uselist=True)

    # table constraints
    __table_args__ = (
        CheckConstraint('min_cgpa >= 0.0 AND min_cgpa <= 10.0', name="drive_eligibility_cgpa_range"),
    )


db.Table(
    "drive_eligibility_branches",
    db.Column("eligibility_id", db.Integer, db.ForeignKey("drive_eligibility.id"), primary_key=True),
    db.Column("branch_id", db.Integer, db.ForeignKey("branch.id"), primary_key=True)
)

################################################################
# STRUCTURAL FILLER CLASSES
################################################################

class User(db.Model):
    """
    Base user class for all user types. This is an abstract class and will not be mapped to a table. It contains common fields and relationships for all user types. Both Student and Company will inherit from this class. I will write somthing later.

    Admin will be a special user with user_type='admin' and one and only directly mapped to User table. Admin will not have any additional fields or relationships.
    """
    __tablename__ = "user"

    # authentication fields
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(255), nullable=False, unique=True)
    password=db.Column(db.String(255), nullable=False)          # argon hashed
    is_active=db.Column(db.Boolean, nullable=False, default=True)
    created_at=db.Column(db.DateTime, nullable=False, default=lambda:datetime.now(timezone.utc))
    last_login=db.Column(db.DateTime, nullable=True)
    user_type=db.Column(db.Enum(UserType), nullable=False)

    otp = db.Column(db.String(6), nullable=True) 
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    last_otp_sent_at = db.Column(db.DateTime, nullable=True)

    reset_token = db.Column(db.String(128), nullable=True, unique=True)
    reset_token_expires_at = db.Column(db.DateTime, nullable=True)


    # common profile fields
    name=db.Column(db.String(63), nullable=False)
    profile_photo=db.Column(db.String(255), nullable=True, default="user.png")  # address

    # table constraints
    __table_args__ = (
        db.Index("idx_user_type_active", "user_type", "is_active"),
    )

    # mapper args
    __mapper_args__ = {
        "polymorphic_on":user_type,
        "polymorphic_identity": UserType.admin
    }


###############################################################
# CONCRETE CLASSES -> ENTITIES
###############################################################


class Student(User):
    """
    Docstring for Student
    """
    __tablename__ = "student"

    # student specific fields
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.Enum(Gender), nullable=False)

    # college specific fields
    roll = db.Column(db.String(10), unique=True, nullable=False, index=True)
    admission_year = db.Column(db.Integer, nullable=False)
    current_level = db.Column(db.Integer, nullable=False)   # year of study
    prog_id = db.Column(db.Integer, db.ForeignKey("programme.id"), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey("branch.id"), nullable=False)
    cgpa = db.Column(db.Float, nullable=False, default=0.0)

    # computed properties
    @property
    def age(self):
        today = datetime.now().date()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
    
    # relationships
    programme = db.relationship("Programme", lazy="joined", uselist=False, back_populates="students")
    branch = db.relationship("Branch", lazy="joined", uselist=False, back_populates="students")
    applications = db.relationship("Application", back_populates="student", lazy="selectin", uselist=True)

    # table constraints
    __table_args__ = (
        CheckConstraint('current_level >= 1', name="student_current_level_positive"),
        CheckConstraint('cgpa >= 0.0 AND cgpa <= 10.0', name="student_cgpa_valid"),
        # check that current_level <= programme.duration_years in application logic
        CheckConstraint('admission_year >= 2000', name="student_admission_year_valid"),
        db.Index("idx_student_programme", "prog_id"),
        db.Index("idx_student_branch", "branch_id"),
        db.Index("idx_student_year_level", "current_level", "admission_year"),
        # 
    )
    
    # mapper args
    __mapper_args__ = {
        "polymorphic_identity": UserType.student
    }

class Company(User):
    """
    Company representing an employer entity. I will write somthing later.
    """
    __tablename__ = "company"

    # authorazation fields
    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)

    # company specific fields
    industry = db.Column(db.String(63), nullable=False)
    description = db.Column(db.String(), nullable=False)
    website = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False, unique=True)

    # relationships
    placement_drive = db.relationship("PlacementDrive", back_populates="company", lazy="selectin", uselist=True)
    applications = db.relationship("Application",
                                   secondary="placement_drive",
                                   primaryjoin="Company.id == PlacementDrive.company_id",
                                   secondaryjoin="PlacementDrive.id == Application.drive_id",
                                   viewonly=True,
                                   lazy="selectin",
                                   uselist=True)
    
    # table constraints
    __table_args__ = (
        CheckConstraint('length(contact_number) >= 7 AND length(contact_number) <= 15', name="company_contact_number_length"),
        db.Index("idx_company_approval", "is_approved"),

    )
    # mapper args
    __mapper_args__ = {
        "polymorphic_identity": UserType.company
    }


class PlacementDrive(db.Model):         # Job role -> many vaccancies
    """
    Docstring for PlacementDrive
    """
    __tablename__ = "placement_drive"

    # placement drive identification and approval fields
    id=db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    approval_status=db.Column(db.Enum(DriveApprovalStatus), nullable=False, default=DriveApprovalStatus.pending)
    status=db.Column(db.Enum(DriveStatus), nullable=False, default=DriveStatus.upcoming)

    # placement drive details
    title=db.Column(db.String(63), nullable=False)
    description=db.Column(db.String(), nullable=False)
    work_mode=db.Column(db.Enum(WorkMode), nullable=False)
    job_location = db.Column(db.String(255), nullable=False)
    eligibility=db.Column(db.Integer, db.ForeignKey("drive_eligibility.id"), nullable=False)
    number_of_vacancies = db.Column(db.Integer, nullable=False)
    opening=db.Column(db.DateTime(), nullable=False)   
    deadline=db.Column(db.DateTime(), nullable=False)

    # properties
    @property
    def is_open(self):
        now = datetime.now(timezone.utc)
        return self.opening <= now <= self.deadline
    
    @property
    def is_expired(self):
        now = datetime.now(timezone.utc)
        return now > self.deadline

    # relationships
    company = db.relationship("Company", back_populates="placement_drive", uselist=False, lazy="joined")
    drive_eligibility = db.relationship("DriveEligibility", uselist=False, lazy="joined")
    applications = db.relationship("Application", back_populates="placement_drive", lazy="selectin", uselist=True)

    # table constraints
    __table_args__ = (
        UniqueConstraint('company_id', 'title', name='unique_company_drive_title'),
        CheckConstraint('number_of_vacancies > 0', name="placement_drive_positive_vacancies"),
        CheckConstraint('deadline > opening', name="placement_drive_deadline_after_opening"),
        CheckConstraint('length(job_location) > 0', name="placement_drive_job_location_not_empty"),

        db.Index("idx_placement_drive_status","approval_status", "status", "opening"),
        db.Index("idx_placement_work_mode","work_mode"),
        db.Index("idx_placement_drive_company","company_id"),
    )


class Application(db.Model):
    """
    Docstring for Application
    """
    __tablename__ = "application"

    # application identification fields and status
    id=db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id", ondelete="cascade"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drive.id", ondelete="cascade"), nullable=False)
    applied_on=db.Column(db.DateTime(), nullable=False, default=lambda:datetime.now(timezone.utc))
    status=db.Column(db.Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.applied)
    status_updated_on=db.Column(db.DateTime(), nullable=False, default=lambda:datetime.now(timezone.utc))
    resume_url=db.Column(db.String(255), nullable=False)
    remarks=db.Column(db.String(), nullable=True)

    # relationships
    placement_drive=db.relationship("PlacementDrive", lazy="joined", back_populates="applications")
    student=db.relationship("Student", lazy="joined", back_populates="applications")
    company = db.relationship(
        "Company",
        secondary="placement_drive",
        primaryjoin="Application.drive_id == PlacementDrive.id",
        secondaryjoin="PlacementDrive.company_id == Company.id",
        viewonly=True,
        lazy="joined"
    )

    # table constraints
    __table_args__ = (
        UniqueConstraint('student_id', 'drive_id', name='unique_student_drive_application'),
        db.Index("idx_application_student", "student_id"),
        db.Index("idx_application_drive", "drive_id"),
        db.Index("idx_application_status", "status"),
        db.Index("idx_application_applied_on", "student_id", "applied_on"),
    )


#########################################################################
# Events and Triggers
#########################################################################

# Immutable Student roll number
@event.listens_for(Student, "before_update")
def prevent_roll_change(mapper, connection, target):
    if db.inspect(target).attrs.roll.history.has_changes():
        raise ValueError("Student roll number cannot be changed")

# Branch Code Validation
@event.listens_for(Branch, "before_insert")
def validate_branch_code(mapper, connection, target):
    result = connection.execute(
        db.select(Programme.code).where(Programme.id == target.prog_id)
    ).scalar_one_or_none()

    if result is None:
        raise ValueError("Invalid programme reference")

    if not target.code.startswith(result):
        print(result)
        print(target.code)
        raise ValueError("Invalid branch code")


# Immutable Branch Code
@event.listens_for(Branch, "before_update")
def prevent_branch_code_change(mapper, connection, target):
    if db.inspect(target).attrs.code.history.has_changes():
        raise ValueError("Branch code cannot be changed")

# Immutable Programme Code
@event.listens_for(Programme, "before_update")
def prevent_progamme_code_change(mapper, connection, target):
    if db.inspect(target).attrs.code.history.has_changes():
        raise ValueError("Programme code cannot be changed")

# Immutable Company Id in PlacementDrive
@event.listens_for(PlacementDrive, "before_update")
def prevent_company_drive_change(mapper, conn, target):
    if db.inspect(target).attrs.company_id.history.has_changes():
        raise ValueError("company_id is immutable")

# Immutable Drive Id in Application
@event.listens_for(Application, "before_update")
def prevent_drive_application_change(mapper, conn, target):
    if db.inspect(target).attrs.drive_id.history.has_changes():
        raise ValueError("drive_id is immutable")

# Immutable Student Id in Application
@event.listens_for(Application, "before_update")
def prevent_student_application_change(mapper, conn, target):
    if db.inspect(target).attrs.student_id.history.has_changes():
        raise ValueError("student_id is immutable")

# Auto-update Application status_updated_on timestamp
@event.listens_for(Application.status, "set")
def update_status_timestamp(target, value, oldvalue, initiator):
    if value != oldvalue:
        target.status_updated_on = datetime.now(timezone.utc)



## Module Exports
__all__ = [
            "UserType", "DriveApprovalStatus", "DriveStatus", "WorkMode", "ApplicationStatus", "Gender", "DriveEligibility", 
            "Programme", "Branch", "User", "Student", "Company", "PlacementDrive", "Application"]