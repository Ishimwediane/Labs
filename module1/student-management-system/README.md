# Student Course Management System

A Python-based command-line application for managing students, courses, enrollments, and grades in an educational institution.

## Features

- **Student Management**: Add and manage undergraduate and graduate students
- **Course Management**: Create courses with specific level and field requirements
- **Enrollment System**: Enroll students in courses with eligibility validation
- **Grading System**: Set and track student grades with automatic GPA calculation
- **Academic Status**: Automatic classification based on performance (First Class, Second Upper, etc.)
- **Transcripts**: Generate detailed student transcripts with all courses and grades

## Project Structure

```
student-management-system/
├── main.py                 # Application entry point
├── cli/
│   └── menu.py            # Command-line interface and menu system
├── models/
│   ├── student.py         # Student classes (Abstract, Undergraduate, Graduate)
│   ├── course.py          # Course class with enrollment logic
│   ├── enrollment.py      # Enrollment relationship class
│   ├── enums.py           # Level and FieldOfStudy enumerations
└── README.md              # This file
```

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd student-management-system
```

2. **Requirements**: Python 3.10 or higher (uses type hints with `list[Type]` syntax)

3. **No external dependencies required** - uses only Python standard library

## Usage

Run the application:
```bash
python main.py
```

### Menu Options

```
1. Add Student              - Create new undergraduate or graduate student
2. Add Course               - Create course with level/field restrictions
3. Enroll Student in Course - Enroll eligible students in courses
4. Set Grade for Student    - Assign grades (0-100) to enrolled students
5. List Students in Course  - View all students enrolled in a course
6. Show Student Transcript  - Display student's grades and academic status
7. Update Course            - Modify course details
8. Remove Student from Course - Unenroll a student
9. List All Courses         - View all available courses
10. List All Students       - View all registered students
0. Exit                     - Close the application
```

## Data Models

### Student (Abstract Base Class)
**Attributes:**
- `name`: Student's full name (letters and spaces only)
- `student_id`: Unique identifier
- `gender`: Male or female
- `email`: Valid email address
- `level`: UNDERGRADUATE or GRADUATE
- `field_of_studies`: Academic field (Science, Arts, Commerce, Engineering, Medicine, Law)
- `course_grades`: Dictionary of course grades

**Subclasses:**
- `Undergraduate`: Students at undergraduate level
- `Graduate`: Students at graduate level

### Course
**Attributes:**
- `title`: Course name (letters and spaces only)
- `course_id`: Unique course identifier
- `allowed_levels`: List of eligible student levels
- `allowed_fields`: List of eligible fields of study
- `enrollments`: List of enrolled students with grades

**Methods:**
- `enroll(student)`: Enroll a student if eligible
- `set_grade(student, grade)`: Assign grade (0-100)
- `remove_student(student)`: Unenroll a student
- `list_students()`: Display all enrolled students
- `average_grade()`: Calculate course average

### Enrollment
Represents the relationship between a student and a course, storing the grade.

## Examples

### Adding a Student
```
Select an option: 1
Name: John Doe
Student ID: ST001
Gender: male
Email: john.doe@university.edu
Available Levels: ['undergraduate', 'graduate']
Level: undergraduate
Available Fields: ['science', 'arts', 'commerce', 'engineering', 'medicine', 'law']
Field of study: engineering
Student added: John Doe (undergraduate)
```

### Adding a Course with Multiple Fields
```
Select an option: 2
Course title: Advanced Mathematics
Course ID: MATH301
Available Levels: ['undergraduate', 'graduate']
Allowed Level(s) [separate multiple with comma, or type 'all']: graduate
Available Fields: ['science', 'arts', 'commerce', 'engineering', 'medicine', 'law']
Allowed Field(s) [separate multiple with comma, or type 'all']: science,engineering
Course added: Advanced Mathematics (MATH301)
  Allowed Levels: ['graduate']
  Allowed Fields: ['science', 'engineering']
```

### Viewing Student Transcript
```
Select an option: 6
Student ID: ST001

Transcript - John Doe (ST001)
---------------------------------------------
MATH301: 85
PHY201: 78
ENG101: Not yet graded
---------------------------------------------
Total Average: 81.50
Academic Status: First Class
```

## Academic Status Classification

| Average Grade | Classification |
|--------------|----------------|
| 80-100 | First Class |
| 70-79 | Second Upper Class |
| 60-69 | Second Lower Class |
| 50-59 | Pass |
| 0-49 | Fail |

## Validation Rules

### Student Validation
- **Name**: Cannot be empty, letters and spaces only
- **Student ID**: Cannot be empty
- **Gender**: Must be "male" or "female"
- **Email**: Must contain "@" and "."
- **Level**: Must be valid Level enum (UNDERGRADUATE or GRADUATE)
- **Field of Study**: Must be valid FieldOfStudy enum

### Course Validation
- **Title**: Cannot be empty, letters and spaces only
- **Allowed Levels**: Must be a list of Level enums
- **Allowed Fields**: Must be a list of FieldOfStudy enums

### Grade Validation
- Must be a number between 0 and 100
- Student must be enrolled in the course

### Enrollment Validation
- Student's level must match course's allowed levels
- Student's field must match course's allowed fields
- Student cannot be enrolled twice in the same course

## Technical Implementation Details

### Key Problem Solved: Property Setter Validation

**Problem Encountered:**
Initially, the `__init__` constructor was directly assigning values to private attributes:
```python
def __init__(self, name, student_id, gender, email, ...):
    self._name = name          
    self._student_id = student_id
    self._gender = gender
    self._email = email
```

This approach **completely bypassed all property setter validations**, allowing invalid data to be stored:
- Empty names were accepted
- Invalid emails like "a@." were stored
- Any gender value was allowed
- No validation occurred at object creation time

**Root Cause:**
When you assign directly to `self._name`, Python treats it as a direct attribute assignment to the private variable, **not** as a call to the `name` property setter. The setter validation code was never executed.

**Solution:**
The constructor was modified to call the **property setters** instead of directly assigning to private attributes:
```python
def __init__(self, name, student_id, gender, email, ...):
    self.name = name               # Calls name.setter with validation
    self.gender = gender           # Calls gender.setter
    self.email = email             # Calls email.setter
```

When you assign to `self.name`, Python automatically calls the `name.setter` method, which:
1. Runs all validation checks
2. Raises `ValueError` if data is invalid
3. Assigns to `self._name` only if validation passes

**Key Lesson:**
- Use `self.name = value` in `__init__` to trigger setter validation
- **Never** use `self._name = value` in `__init__` (bypasses validation)
- Private attributes (`_name`, `_email`) are still used internally for storage
- Setters handle both validation **and** assignment to private attributes
- Single source of truth for validation logic (no duplication needed)



### Design Patterns Used

1. **Abstract Base Class**: `Student` is abstract with `Undergraduate` and `Graduate` subclasses
2. **Encapsulation**: Private attributes with property decorators for controlled access
3. **Composition**: `Course` contains `Enrollment` objects which reference `Student` objects
4. **Enumeration**: Type-safe level and field of study definitions
5. **Property Decorators**: Validation through getters and setters without duplication

## Error Handling

The system provides clear error messages for:
- Invalid input data (empty fields, wrong formats)
- Duplicate IDs
- Ineligible enrollments
- Grade assignment to non-enrolled students
- Invalid enum values

Example error messages:
```
Error adding student: Name cannot be empty
Error adding student: Invalid email
Error adding student: Gender must be male or female
```

## Future Enhancements

Potential features for future versions:
- [ ] Persistent storage ( file system)
- [ ] Search and filter functionality
- [ ] Attendance tracking
- [ ] Course prerequisites
- [ ] Student and course reports
- [ ] Export transcripts to PDF
- [ ] Multiple grading schemes
- [ ] Teacher/instructor management
- [ ] Course scheduling and timetables

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commit messages
4. Test thoroughly
5. Submit a pull request



## Author

Created as a demonstration of object-oriented programming principles in Python, including:
- Class inheritance and polymorphism
- Property decorators and encapsulation
- Abstract base classes
- Data validation best practices
- CLI design patterns

---

**Note**: This is an educational project demonstrating OOP concepts. For production use, consider adding:
- Database integration (SQLite, PostgreSQL)
- User authentication and authorization
- Web interface (Flask/Django)
- Unit tests and integration tests
- Logging system
- Configuration management