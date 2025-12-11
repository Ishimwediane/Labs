from menu.course_menu import add_course, set_grade, list_students_in_course, update_course, remove_student_from_course, list_all_courses
from menu.student_menu import add_student, show_transcript, list_all_students
from menu.enrollment_menu import enroll_student, enroll_student

def run_cli():
    students = {}
    courses = {}

    menu_options = {
        "1":("Add Student",lambda: add_student(students)),
        "2":("Add Course",lambda: add_course(courses)),
        "3":("Enroll Student",lambda: enroll_student(students, courses)),
        "4":("Set grade for student",lambda: set_grade(students, courses)),
        "5":("List students in course",lambda: list_students_in_course(courses)),
        "6":("show student transcript",lambda: show_transcript(students)),
        "7":("update course",lambda: update_course(courses)),
        "8":("remove student from course",lambda: remove_student_from_course(students, courses)),
        "9":("list all students",lambda: list_all_students(students)),
        "10":("list all courses",lambda: list_all_courses(courses)),
        "0" :("Exit",lambda: print("Exiting..."))
        
             
    }
    
    while True:
        print("\n--- student Enrollment management system---")
        for key,(value,_) in menu_options.items():
            print(f"{key}. {value}")
            
        choice=input("select an option: ").strip()
        
        action=menu_options.get(choice)
        if action:
            if choice=="0":
                break
            action[1]()
        else:print("invalid choice")