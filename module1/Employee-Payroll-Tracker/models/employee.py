from abc import ABC, abstractmethod

class Employee(ABC):
    """Base class for all employee types."""

    _id_counter = 1

    def __init__(self, name: str, department: str, position: str, bonus: float = 0):
        self.name = name
        self._employee_id = Employee._id_counter
        Employee._id_counter += 1
        self.department = department
        self.position = position
        self.bonus = bonus
        self._salary = 0

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not value.strip():
            raise ValueError("Name is required")
        self._name = value

    @property
    def employee_id(self):
        return self._employee_id

    @property
    def salary(self):
        return self._salary

    @salary.setter
    def salary(self, value):
        if value < 0:
            raise ValueError("Salary cannot be negative")
        self._salary = value
        
    @property
    def bonus(self):
        return self._bonus

    @bonus.setter
    def bonus(self, value):
        if value < 0:
            raise ValueError("Bonus cannot be negative")
        self._bonus = value
    @property
    def tax(self):
        """Rwanda progressive income tax based on salary only."""
        s = self._salary
        tax = 0
        if s > 1000000:
            tax += (s - 1000000) * 0.35
            s = 1000000
        if s > 250000:
            tax += (s - 250000) * 0.30
            s = 250000
        if s > 100000:
            tax += (s - 100000) * 0.25
            s = 100000
        if s > 30000:
            tax += (s - 30000) * 0.20
        return tax
    
    @property
    def net_salary(self):
        return self.compute_salary() - self.tax
    

    def update_salary(self, value):
        self.salary = value

    def update_bonus(self, value):
        self.bonus = value

    @abstractmethod
    def compute_salary(self):
        """Compute total salary including bonus."""
        pass

    @abstractmethod
    def generate_payslip(self):
        """Prints employee payslip."""
        pass
