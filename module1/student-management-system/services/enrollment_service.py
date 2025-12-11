from models.enrollment import Enrollment
from models.student import Student
from models.course import Course
from services.student_service import StudentService
from services.course_service import CourseService




class EnrollmentService:
    @staticmethod
    def enroll_student(student: Student, course: Course):
        if student.level not in course.allowed_levels:
            raise ValueError(f"Level '{student.level.value}' not allowed")
        if student.field_of_studies not in course.allowed_fields:
            raise ValueError(f"Field '{student.field_of_studies.value}' not allowed")
        if any(en.student == student for en in course.enrollments):
            raise ValueError("Student already enrolled")
        
        enrollment = Enrollment(student, course)
        course.enrollments.append(enrollment)
        student._course_grades[course.course_id] = None
        return enrollment

    @staticmethod
    def set_grade(student: Student, course: Course, grade):
        enrollment = next((en for en in course.enrollments if en.student == student), None)
        if not enrollment:
            raise ValueError("Student not enrolled in course")
        enrollment.grade = grade
        student._course_grades[course.course_id] = grade

    @staticmethod
    def student_transcript(student: Student, courses: list):
        print(f"\nTranscript for {student.name} ({student.student_id}):")
        for course in courses:
            if course.course_id in student._course_grades:
                grade = student._course_grades[course.course_id]
                print(f"{course.title} - {grade if grade is not None else 'Not graded'}")
        print(f"Total Average: {StudentService.total_average(student):.2f}")
        print(f"Academic Status: {StudentService.academic_status(student)}")
