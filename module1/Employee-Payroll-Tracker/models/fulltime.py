from .employee import Employee


class FullTimeEmployee(Employee):
    """Full-time employee with monthly salary."""

    def __init__(self, name, department, position, monthly_salary, bonus=0):
        super().__init__(name, department, position, bonus)
        self._salary = monthly_salary

    def compute_salary(self):
        return self._salary + self.bonus

    def generate_payslip(self):
        print(f"--- Payslip for Full-Time Employee: {self.name} ---")
        print(f"ID: {self.employee_id} | Department: {self.department} | Position: {self.position}")
        print(f"Gross salary : RWF{self._salary:.2f} | Bonus: RWF{self.bonus:.2f} ")
        print(f"Tax: RWF{self.tax:.2f} | Net salary: RWF{self.net_salary:.2f} ")
        print("-" * 50)

