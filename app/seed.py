from datetime import date, time, timedelta

from app.db import SessionLocal
from app.models import AppUser, AvailabilityWindow, Session, Student, Tutor
from app.security import hash_password

DEMO_PASSWORD = "redgum123"

TUTORS = [
    {
        "name": "Tomás Ferreira",
        "phone": "0407 512 884",
        "subjects": "Physics 10-12, Chemistry 10-12, Maths Methods 11-12",
        "status": "ACTIVE",
        "windows": [
            ("TUESDAY", time(15, 30), time(19, 0)),
            ("WEDNESDAY", time(15, 30), time(18, 0)),
            ("THURSDAY", time(16, 0), time(18, 30)),
            ("SATURDAY", time(9, 0), time(12, 30)),
        ],
    },
    {
        "name": "Helen Vasquez",
        "phone": "0407 220 118",
        "subjects": "Maths 5-12",
        "status": "ACTIVE",
        "windows": [
            ("WEDNESDAY", time(15, 0), time(18, 30)),
            ("SATURDAY", time(9, 0), time(13, 0)),
        ],
    },
    {
        "name": "Priyanka Shah",
        "phone": "0407 883 402",
        "subjects": "Maths 5-10, Science 7-10",
        "status": "ACTIVE",
        "windows": [
            ("TUESDAY", time(16, 0), time(19, 0)),
            ("THURSDAY", time(15, 30), time(18, 0)),
        ],
    },
    {
        "name": "Marcus Webb",
        "phone": "0407 145 990",
        "subjects": "English 7-10",
        "status": "INACTIVE",
        "windows": [("FRIDAY", time(15, 30), time(18, 0))],
    },
]

STUDENTS = [
    {"name": "Ella Nguyen", "year_level": 11, "school": "Limestone High", "contact_name": "Mai Nguyen",
     "contact_phone": "0412 660 118", "contact_email": "mai.nguyen@example.com", "subjects": "Physics"},
    {"name": "Jayden Pike", "year_level": 10, "school": "Limestone High", "contact_name": "Rebecca Pike",
     "contact_phone": "0413 220 774", "contact_email": None, "subjects": "Maths"},
    {"name": "Sara Habib", "year_level": 12, "school": "Ipswich Girls Grammar", "contact_name": "Nadia Habib",
     "contact_phone": "0414 981 205", "contact_email": "nadia.habib@example.com", "subjects": "Chemistry"},
    {"name": "Oliver Brandt", "year_level": 9, "school": "Ipswich State High", "contact_name": "Petra Brandt",
     "contact_phone": "0415 330 619", "contact_email": None, "subjects": "Maths"},
    {"name": "Mia Okafor", "year_level": 12, "school": "Ipswich Girls Grammar", "contact_name": "Chidi Okafor",
     "contact_phone": "0416 774 082", "contact_email": "chidi.okafor@example.com", "subjects": "Maths Methods"},
    {"name": "Kai Lombardo", "year_level": 11, "school": "Willowbank State High", "contact_name": "Gina Lombardo",
     "contact_phone": "0418 330 297", "contact_email": "g.lombardo@example.com", "subjects": "Physics, Maths Methods"},
    {"name": "Noah Fischer", "year_level": 8, "school": "Ipswich State High", "contact_name": "Anna Fischer",
     "contact_phone": "0417 552 361", "contact_email": None, "subjects": "Maths"},
]

# 文档 B(第 5 周,2026-08-11 至 08-15)的原样课时;状态:A=ATTENDED, N=MISSED, C/CANCELLED=CANCELLED
DIARY_WEEK = [
    ("TUE", date(2026, 8, 11), time(15, 30), "Ferreira", "Ella Nguyen", "Physics", 60, "ATTENDED"),
    ("TUE", date(2026, 8, 11), time(16, 45), "Ferreira", "Jayden Pike", "Maths", 60, "MISSED"),
    ("TUE", date(2026, 8, 11), time(18, 0), "Ferreira", "Sara Habib", "Chemistry", 60, "ATTENDED"),
    ("WED", date(2026, 8, 12), time(15, 30), "Vasquez", "Oliver Brandt", "Maths", 60, "ATTENDED"),
    ("WED", date(2026, 8, 12), time(16, 45), "Vasquez", "Mia Okafor", "Maths Methods", 90, "ATTENDED"),
    ("THU", date(2026, 8, 13), time(16, 0), "Ferreira", "Ella Nguyen", "Physics", 60, "ATTENDED"),
    ("THU", date(2026, 8, 13), time(17, 15), "Ferreira", "Kai Lombardo", "Physics", 60, "CANCELLED"),
    ("SAT", date(2026, 8, 15), time(9, 0), "Ferreira", "Jayden Pike", "Maths", 60, "ATTENDED"),
    ("SAT", date(2026, 8, 15), time(10, 15), "Vasquez", "Sara Habib", "Chemistry", 90, "ATTENDED"),
    ("SAT", date(2026, 8, 15), time(12, 0), "Vasquez", "Oliver Brandt", "Maths", 60, "CANCELLED"),
]


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        if db.query(Student).count() > 0 or db.query(AppUser).count() > 0:
            return

        tutors = {}
        for spec in TUTORS:
            tutor = Tutor(name=spec["name"], phone=spec["phone"], subjects=spec["subjects"], status=spec["status"])
            for day, start, end in spec["windows"]:
                tutor.windows.append(AvailabilityWindow(day_of_week=day, start_time=start, end_time=end))
            db.add(tutor)
            tutors[spec["name"].split()[0]] = tutor
            tutors[spec["name"].split()[-1]] = tutor
        db.flush()

        students = {}
        for spec in STUDENTS:
            student = Student(**spec, status="ACTIVE")
            db.add(student)
            students[spec["name"]] = student
        db.flush()

        db.add_all([
            AppUser(username="deb", password_hash=hash_password(DEMO_PASSWORD), role="ADMIN", status="ACTIVE"),
            AppUser(username="helen", password_hash=hash_password(DEMO_PASSWORD), role="ADMIN",
                    tutor_id=tutors["Helen"].id, status="ACTIVE"),
            AppUser(username="tomas", password_hash=hash_password(DEMO_PASSWORD), role="TUTOR",
                    tutor_id=tutors["Tomás"].id, status="ACTIVE"),
        ])

        for _day, session_date, start, tutor_key, student_name, subject, length, status in DIARY_WEEK:
            db.add(Session(
                student_id=students[student_name].id,
                tutor_id=tutors[tutor_key].id,
                subject=subject,
                session_date=session_date,
                start_time=start,
                length_minutes=length,
                status=status,
            ))

        # 下周的 BOOKED 课时(相对今天动态生成),保证任何时间演示都有"即将到来"数据
        today = date.today()
        next_tuesday = today + timedelta(days=(1 - today.weekday()) % 7 or 7)
        upcoming = [
            (next_tuesday, time(15, 30), "Ferreira", "Ella Nguyen", "Physics", 60),
            (next_tuesday, time(16, 45), "Ferreira", "Kai Lombardo", "Physics", 60),
            (next_tuesday, time(18, 0), "Ferreira", "Sara Habib", "Chemistry", 60),
            (next_tuesday + timedelta(days=1), time(15, 30), "Vasquez", "Oliver Brandt", "Maths", 60),
            (next_tuesday + timedelta(days=2), time(16, 0), "Ferreira", "Ella Nguyen", "Physics", 60),
            (next_tuesday + timedelta(days=4), time(9, 0), "Ferreira", "Jayden Pike", "Maths", 60),
        ]
        for session_date, start, tutor_key, student_name, subject, length in upcoming:
            db.add(Session(
                student_id=students[student_name].id,
                tutor_id=tutors[tutor_key].id,
                subject=subject,
                session_date=session_date,
                start_time=start,
                length_minutes=length,
                status="BOOKED",
            ))

        db.commit()
    finally:
        db.close()
