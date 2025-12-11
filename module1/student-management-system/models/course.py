from abc import ABC, abstractmethod
from .student import Student
from .enrollment import Enrollment
from .enums import Level, FieldOfStudy


class Course:
    def __init__(self, title, course_id, allowed_fields, allowed_levels = None):
         
        self.enrollments = []
      
        self._title = None
        self._course_id = course_id
        self.allowed_levels = allowed_levels if allowed_levels is not None else [Level.UNDERGRADUATE, Level.GRADUATE]
        self.allowed_fields = allowed_fields if allowed_fields else list(FieldOfStudy)

        self.title=title

    # Title property 
    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if not value.strip():
            raise ValueError("Course title is required")
        if not value.replace(" ", "").isalpha():
            raise ValueError("Course title can only contain letters and spaces")
        self._title = value

    # Course 
    @property
    def course_id(self):
        return self._course_id

    # Allowed Levels
    @property
    def allowed_levels(self):
        return self._allowed_levels

    @allowed_levels.setter
    def allowed_levels(self, value):
        
        if not isinstance(value, list):
            raise ValueError("allowed_levels must be a list")
        if not all(isinstance(v, Level) for v in value):
            raise ValueError("All items in allowed_levels must be Level enum instances")
        self._allowed_levels = value

    #  Allowed Fields property 
    @property
    def allowed_fields(self):
        return self._allowed_fields

    @allowed_fields.setter
    def allowed_fields(self, value):
        #  Check if value is a list first
        if not isinstance(value, list):
            raise ValueError("allowed_fields must be a list")
        if not all(isinstance(v, FieldOfStudy) for v in value):
            raise ValueError("All items in allowed_fields must be FieldOfStudy enum instances")
        self._allowed_fields = value


    # Remove a student 
    def remove_student(self, student: Student):
        for en in self.enrollments:
            if en.student == student:
                self.enrollments.remove(en)
                if hasattr(student, '_course_grades'):
                    student._course_grades.pop(self.course_id, None)
                print(f"{student.name} removed from {self.title}")
                return
        print(f"{student.name} not enrolled in {self.title}")

    # Set a grade 
    def set_grade(self, student: Student, grade):
        enrollment = next((en for en in self.enrollments if en.student == student), None)
        if not enrollment:
            print(f"{student.name} not enrolled in {self.title}")
            return
        if not (0 <= grade <= 100):
            raise ValueError("Grade must be 0-100")
        enrollment.grade = grade
        if not hasattr(student, '_course_grades'):
            student._course_grades = {}
        student._course_grades[self.course_id] = grade
        print(f"Grade {grade} set for {student.name} in {self.title}")



    # Update course attributes 
    def update_course(self, **kwargs):
        for key, value in kwargs.items():
            attr = f"_{key}"
            if hasattr(self, attr):
                setattr(self, attr, value)
            else:
                print(f"Attribute '{key}' not found")
        print(f"Course {self.course_id} updated")

    def __str__(self):
        return f"{self.title} ({self.course_id}) - {len(self.enrollments)} students"