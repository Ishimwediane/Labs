from models.student import Undergraduate, Graduate
from models.course import Course
from models.enums import Level, FieldOfStudy
from services.student_service import StudentService

def add_student(students: dict):
    name = input("Name: ").strip()
    student_id = input("Student ID: ").strip()

    if student_id in students:
        print("Student ID already exists!")
        return

    gender = input("Gender (male/female): ").strip()
    email = input("Email: ").strip()

    print(f"Available Levels: {[lvl.value for lvl in Level]}")
    level_input = input("Level: ").strip().lower()

    print(f"Available Fields: {[f.value for f in FieldOfStudy]}")
    field_input = input("Field of study: ").strip().lower()

    try:
        student=StudentService.add_student(students, name, student_id, gender, email, level_input, field_input)
        print(f"Student added: {student.name} ({student.student_id})")
    
    except ValueError as e:
        print(e)
        return
    

def show_transcript(students):
    sid = input("Student ID: ").strip()
    student = students.get(sid)

    if student:
        student.transcript()
    else:
        print("Student not found.")


def list_all_students(students):
    if not students:
        print("No students found.")
    else:
        for s in students.values():
            print(f"{s.student_id}: {s.name} | {s.level.value} | {s.field_of_studies.value}")

