from .student import Student

class Enrollment:
    """
    Represents the enrollment of a student in a course, along with their grade.
    """
    def __init__(self, student: Student,course):
        self._student = student
        self._grade = None
        self._course = course

    # Student
    @property
    def student(self):
        return self._student
    
    #course
    @property
    def course(self):
        return self._course

    # Grade
    @property
    def grade(self):
        return self._grade

    @grade.setter
    def grade(self, value):   
        if not (0 <= value <= 100):
            raise ValueError("Grade must be between 0 and 100")
        self._grade = value


    def __str__(self):
        grade_display = self.grade if self.grade is not None else "Not graded"
        return f"{self.student.name} ({self.student.field_of_studies.value}) - Grade: {grade_display}"
