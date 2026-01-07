from dataclasses import dataclass, field
from typing import List
from collections import namedtuple


TopPerformer = namedtuple("TopPerformer", ["name", "average_score"])

from enum import Enum

class GradeCategory(Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    AVERAGE = "Average"
    PASS = "Pass"
    FAIL = "Fail"

@dataclass(frozen=True)
class Grade:
    """Represents a grade value and its category."""
    score: float
    category: GradeCategory

@dataclass(frozen=True)
class Course:
    """Represents a course achievement."""
    course_name: str
    grade: Grade 

@dataclass
class Student:
    """Represents a student and their course grades."""
    student_id: str
    name: str
    major: str
    year: int
    is_active: bool = True
    courses: List[Course] = field(default_factory=list)
