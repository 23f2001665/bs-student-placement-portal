# Error/Suggestions

- placement-drive may also include the opening date.
- placement-drive may be in relationship with elibility table for more verbosity.
- drive status should be upcoming/active/closed/cancelled or something like this.
- application status should be applied/short-listed/accepted/rejected like this.
- 

Perfect, this is the **final hardening step**.
Indexes are where you *actually* make SQLite feel fast.

I’ll do this in a **very deliberate, minimal, and justified way** — no cargo-cult indexing.

---

# First: SQLite indexing rules (important context)

SQLite:

* ❌ does NOT auto-index foreign keys
* ❌ does NOT optimize joins magically
* ✅ benefits massively from **composite + status indexes**
* ❌ too many indexes slow down writes (but your system is read-heavy)

So we index for:

* dashboards
* filters
* joins
* uniqueness enforcement

---

# Indexing strategy (mental model)

> **Index columns that appear in**
>
> * WHERE
> * JOIN
> * ORDER BY
> * frequent dashboard counts

Do **not** index:

* booleans alone
* low-cardinality enums alone (unless combined)

---

# 1️⃣ `Programme` — ✅ minimal indexing

```python
class Programme(db.Model):
    __tablename__ = "programme"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(7), nullable=False, unique=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.Index("idx_programme_active", "is_active"),
    )
```

### Why

* Admin will filter active programmes
* `code` already indexed via `unique=True`

---

# 2️⃣ `Branch` — ✅ essential indexes

```python
class Branch(db.Model):
    ...

    prog_id = db.Column(db.Integer, db.ForeignKey("programme.id"), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False)

    __table_args__ = (
        db.Index("idx_branch_programme", "prog_id"),
        db.Index("idx_branch_active", "is_active"),
    )
```

### Why

* Programme → Branch lookup
* Filtering active branches

---

# 3️⃣ `User` — ✅ very important

```python
class User(db.Model):
    ...

    email = db.Column(db.String(255), nullable=False, unique=True)
    user_type = db.Column(db.Enum(UserType), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False)

    __table_args__ = (
        db.Index("idx_user_type_active", "user_type", "is_active"),
    )
```

### Why

* Admin dashboards by role
* Auth filters
* Combined index is critical

---

# 4️⃣ `Student` — ✅ dashboard & filtering

```python
class Student(User):
    ...

    prog_id = db.Column(db.Integer, db.ForeignKey("programme.id"), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey("branch.id"), nullable=False)
    admission_year = db.Column(db.Integer, nullable=False)
    current_level = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("current_level >= 1", name="student_current_level_positive"),
        db.Index("idx_student_programme", "prog_id"),
        db.Index("idx_student_branch", "branch_id"),
        db.Index("idx_student_year_level", "admission_year", "current_level"),
    )
```

### Why

* Eligibility filtering
* Admin search
* Drive matching

---

# 5️⃣ `Company` — ✅ moderate indexing

```python
class Company(User):
    ...

    is_approved = db.Column(db.Boolean, nullable=False, default=False)

    __table_args__ = (
        db.Index("idx_company_approved", "is_approved"),
    )
```

### Why

* Admin approval queue
* Approved-company filters

---

# 6️⃣ `PlacementDrive` — ⭐ MOST IMPORTANT

This table drives **everything**.

```python
class PlacementDrive(db.Model):
    ...

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    approval_status = db.Column(db.Enum(DriveApprovalStatus), nullable=False)
    status = db.Column(db.Enum(DriveStatus), nullable=False)
    opening = db.Column(db.DateTime(), nullable=False)
    deadline = db.Column(db.DateTime(), nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "title", name="unique_company_drive_title"),

        db.Index("idx_drive_company", "company_id"),
        db.Index("idx_drive_approval_status", "approval_status"),
        db.Index("idx_drive_status", "status"),

        # 🔥 Composite index for student dashboard
        db.Index(
            "idx_drive_open_approved",
            "approval_status",
            "status",
            "deadline"
        ),
    )
```

### Why

* Student dashboard → approved + active + deadline
* Company dashboard → company_id
* Admin approvals

This composite index is **huge** for performance.

---

# 7️⃣ `Application` — ⭐⭐ CRITICAL

```python
class Application(db.Model):
    ...

    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drive.id"), nullable=False)
    status = db.Column(db.Enum(ApplicationStatus), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "drive_id",
            name="unique_student_drive_application"
        ),

        db.Index("idx_application_student", "student_id"),
        db.Index("idx_application_drive", "drive_id"),
        db.Index("idx_application_status", "status"),

        # 🔥 Company dashboard & reports
        db.Index(
            "idx_application_drive_status",
            "drive_id",
            "status"
        ),
    )
```

### Why

* Student history
* Company shortlisting
* Admin reports
* CSV export

---

# ✅ FINAL INDEX SUMMARY (count)

| Table          | Index Count |
| -------------- | ----------- |
| Programme      | 1           |
| Branch         | 2           |
| User           | 1           |
| Student        | 3           |
| Company        | 1           |
| PlacementDrive | 4           |
| Application    | 4           |

**Total ≈ 16 indexes**
This is **perfectly reasonable** for SQLite.

---

# 🎯 Examiner-proof explanation

If asked:

> “Isn’t this too many indexes?”

You answer:

> “Indexes are placed only on foreign keys and frequently filtered columns.
> The system is read-heavy, SQLite doesn’t auto-index FKs, and composite indexes are used only where query patterns justify them.”

That’s a **very strong systems answer**.

---

## Where you stand now

✔ Schema correctness
✔ Invariants enforced
✔ Constraints balanced
✔ Indexes optimized
✔ SQLite-aware design

You are **done with models**.
Next logical steps (if you want):

* Redis caching strategy
* Celery job queries
* API endpoint ↔ index mapping
* Final viva checklist
