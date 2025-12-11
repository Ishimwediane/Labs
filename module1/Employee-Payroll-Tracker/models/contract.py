from .employee import Employee

class ContractEmployee(Employee):
    """Contract employee paid per hour."""

    def __init__(self, name, department, position, hours_worked, hourly_rate, bonus=0):
        super().__init__(name, department, position, bonus)
        self.hours_worked = hours_worked
        self.hourly_rate = hourly_rate

    def compute_salary(self):
        return self.hours_worked * self.hourly_rate + self.bonus

    def generate_payslip(self):
        print(f"--- Payslip for Contract Employee: {self.name} ---")
        print(f"ID: {self.employee_id} | Department: {self.department} | Position: {self.position}")
        print(f"Hours Worked: {self.hours_worked} | Rate: ${self.hourly_rate:.2f}")
        print(f"Gross salary : RWF{self.salary():.2f} | Bonus: RWF{self.bonus:.2f} ")
        print(f"Tax: RWF{self.tax:.2f} | Net salary: RWF{self.net_salary:.2f} ")
        print("-" * 50) 
       
