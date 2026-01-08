from .employee import Employee


class Intern(Employee):
    """Intern employee with fixed stipend."""

    def __init__(self, name, department, position, stipend):
        super().__init__(name, department, position)
        self._salary = stipend

    def compute_salary(self):
        return self._salary

    def generate_payslip(self):
        print(f"--- Payslip for Intern: {self.name} ---")
        print(f"ID: {self.employee_id} | Department: {self.department} | Position: {self.position}")
        print(f"Stipend: ${self._salary:.2f} | Total: ${self.compute_salary():.2f}")
        print("-" * 50)
