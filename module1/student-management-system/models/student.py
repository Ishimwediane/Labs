from abc import ABC, abstractmethod
from .enums import Level, FieldOfStudy

class Student(ABC):
    """
    Abstract Base Class for a Student
    """
    def __init__(self, name, student_id, gender, email, field_of_studies: FieldOfStudy, level: Level = Level.UNDERGRADUATE):
        
        self._name=None
        self._student_id=None
        self._gender=None
        self._email=None
        self._level=None
        self._field_of_studies=None
        
        
        
        self.name = name
        self.student_id = student_id
        self.gender = gender
        self.email = email
        self.level = level
        self.field_of_studies = field_of_studies

    # Name
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        if not value.strip():
            raise ValueError("Name cannot be empty")
        if not value.replace(" ", "").isalpha():
            raise ValueError("Name can only contain letters and spaces")
        self._name = value

    # Gender
    @property
    def gender(self):
        return self._gender
    
    @gender.setter
    def gender(self, value):
        value = value.lower()
        if value not in ("male", "female"):
            raise ValueError("Gender must be male or female")
        self._gender = value

    # Email
    @property
    def email(self):
        return self._email
    
    @email.setter
    def email(self, value):
        if "@" not in value or "." not in value:
            raise ValueError("Invalid email")
        self._email = value

    # Student ID
    @property
    def student_id(self):
        return self._student_id
    
    @student_id.setter
    def student_id(self, value):
        if not value.strip():
            raise ValueError("Student ID cannot be empty")
        self._student_id = value
    
    # Level
    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        if not isinstance(value, Level):
            raise ValueError("Invalid level")
        self._level = value
    
    # Field of Study
    @property
    def field_of_studies(self):
        return self._field_of_studies

    @field_of_studies.setter
    def field_of_studies(self, value):
        if not isinstance(value, FieldOfStudy):
            raise ValueError("Invalid field of study")
        self._field_of_studies = value

  
  
 
    def __str__(self):
        return f"{self._name} ({self._student_id}) - {self._level.value}"
    
    def __repr__(self):
        return f"Student(student_id='{self._student_id}', name='{self._name}')"
    
    def __eq__(self, other):
        return isinstance(other, Student) and self._student_id == other._student_id


# Subclasses
class Undergraduate(Student):
    def __init__(self, name, student_id, gender, email, field_of_studies):
        super().__init__(name, student_id, gender, email, field_of_studies, level=Level.UNDERGRADUATE)

    def __str__(self):
        return f"{self.name} - Undergraduate in {self._field_of_studies.value}"


class Graduate(Student):
    def __init__(self, name, student_id, gender, email, field_of_studies):
        super().__init__(name, student_id, gender, email, field_of_studies, level=Level.GRADUATE)
        
    def __str__(self):
        return f"{self.name} - Graduate in {self._field_of_studies.value}"