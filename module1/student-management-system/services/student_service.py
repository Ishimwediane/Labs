from models.student import Undergraduate, Graduate, Student
from models.enums import Level, FieldOfStudy

class StudentService:
    @staticmethod
    def add_student(students: dict, name, student_id, gender, email, level_input, field_input):
        if student_id in students:
            raise ValueError("Student ID already exists")
        
        try:
            level = Level(level_input)
        except ValueError:
            raise ValueError("Invalid level")
        

        try:
            field = FieldOfStudy(field_input)
        except ValueError:
            raise ValueError("Invalid field")
        
        if level == Level.UNDERGRADUATE:
            student = Undergraduate(name, student_id, gender, email, field) 
        else:
            student = Graduate(name, student_id, gender, email, field)
        
        students[student_id] = student
        return student

    @staticmethod
    def get_student(students: dict, student_id: str):
        return students.get(student_id)

    @staticmethod
    def total_average(student: Student):
        grades = [grade for grade in student._course_grades.values() if grade is not None]
        return sum(grades)/len(grades) if grades else 0

    @staticmethod
    def academic_status(student: Student):
        avg = StudentService.total_average(student)
        if avg >= 80:
            return "First Class"
        elif avg >= 70:
            return "Second Upper Class"
        elif avg >= 60:
            return "Second Lower Class"
        elif avg >= 50:
            return "Pass"
        return "Fail"
