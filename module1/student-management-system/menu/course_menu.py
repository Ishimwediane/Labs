from models.student import Undergraduate, Graduate
from models.course import Course
from models.enums import Level, FieldOfStudy
from services.course_service import CourseService

def add_course(courses: dict):
    title = input("Course title: ").strip()
    course_id = input("Course ID: ").strip()

    if course_id in courses:
        print("Course ID already exists!")
        return

    print(f"Available Levels: {[lvl.value for lvl in Level]}")
    level_input = input("Allowed Level: ").strip().lower()

  
    print(f"Available Fields: {[f.value for f in FieldOfStudy]}")
    field_input = input("Allowed Field: ").strip().lower()

   
    try:  
       course = CourseService.add_course(courses,title, course_id, field_input, level_input)
      
    except ValueError as e:
        print(e)
        return


    print(f"Course added: {course.title} ({course.course_id})")

def set_grade(students, courses):
    sid = input("Student ID: ").strip()
    cid = input("Course ID: ").strip()

    try:
        grade = float(input("Grade (0-100): ").strip())
    except ValueError:
        print("Invalid grade.")
        return

    student = students.get(sid)
    course = courses.get(cid)

    if student and course:
        course.set_grade(student, grade)
    else:
        print("Student or Course not found.")

def list_students_in_course(courses):
    cid = input("Course ID: ").strip()
    course = courses.get(cid)

    if not course:
        print("Course not found.")
        return

    try:
        enrollments = CourseService.list_students(course)
        if not enrollments:
            print("No students enrolled in this course.")
            return
        
        print(f"\nStudents in {course.title}:")
        for e in enrollments:
            s = e.student
            grade = e.grade
            print(f"{s.student_id}: {s.name} | Level: {s.level.value} | Field: {s.field_of_studies.value} | Grade: {grade}")

    except ValueError as e:
        print(e)
 
    

def update_course(courses):
    cid = input("Course ID to update: ").strip()
    course = courses.get(cid)

    if course:
        new_title = input("New Title (blank: skip): ").strip()
        if new_title:
            course.update_course(title=new_title)
    else:
        print("Course not found.")


def remove_student_from_course(students, courses):
    sid = input("Student ID: ").strip()
    cid = input("Course ID: ").strip()

    student = students.get(sid)
    course = courses.get(cid)

    if student and course:
        course.remove_student(student)
    else:
        print("Student or Course not found.")


def list_all_courses(courses):
    if not courses:
        print("No courses available.")
    else:
        for c in courses.values():
            print(f"{c.course_id} - {c.title}")

