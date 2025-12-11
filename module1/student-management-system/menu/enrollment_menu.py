from models.student import Undergraduate, Graduate
from models.course import Course
from models.enums import Level, FieldOfStudy
from services.enrollment_service import EnrollmentService

def enroll_student(students, courses):
    sid = input("Student ID: ").strip()
    cid = input("Course ID: ").strip()

    student = students.get(sid)
    course = courses.get(cid)

    if not student or not course:
        print("Student or Course not found.")
        return
        
    try:
        EnrollmentService.enroll_student(student, course)
        print(f"{student.name} enrolled in {course.title}")
    except ValueError as e:
        print(e)

       
        
    

