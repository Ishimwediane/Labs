from models.employee import Employee

class Payroll:
    """Manages a list of employees and payroll operations."""

    def __init__(self):
        self.employees = {}

    def add_employee(self, employee: Employee):
        if employee.employee_id in self.employees:
            print(f"Employee {employee.name} already exists.")
        else:
            self.employees[employee.employee_id] = employee
            print(f"Employee {employee.name} added.")

    def remove_employee(self, emp_id):
        if emp_id in self.employees:
            removed = self.employees.pop(emp_id)
            print(f"Employee {removed.name} removed.")
        else:
            print("Employee not found")

    def get_employee(self, emp_id):
        return self.employees.get(emp_id)

    def update_salary(self, emp_id, new_salary):
        emp = self.get_employee(emp_id)
        if emp:
            emp.update_salary(new_salary)
            print(f"{emp.name}'s salary updated.")
        else:
            print("Employee not found")

    def update_bonus(self, emp_id, new_bonus):
        emp = self.get_employee(emp_id)
        if emp:
            emp.update_bonus(new_bonus)
            print(f"{emp.name}'s bonus updated.")
        else:
            print("Employee not found")

    def generate_all_payslips(self):
        if not self.employees:
            print("No employees to generate payslips.")
            return
        for emp in self.employees.values():
            emp.generate_payslip()

    def summary_report(self):
        print("Payroll Summary Report")
        print("=" * 60)
        for emp in self.employees.values():
            print(f"{emp.employee_id} | {emp.name} | {emp.department} | {emp.position} | Total: ${emp.compute_salary():.2f}")
        print("=" * 60)
        
    def total_gross_salary(self):
        """Sum of all employees' gross salary (including bonus)."""
        total = sum(emp.compute_salary() for emp in self.employees.values())
        print(f"Total Gross Salary for all employees: RWF {total:.2f}")
        return total

    def total_tax(self):
        """Sum of all taxes deducted from employees."""
        total = sum(emp.tax for emp in self.employees.values())
        print(f"Total Tax to be deducted for all employees: RWF {total:.2f}")
        return total

    def total_net_salary(self):
        """Sum of all net salaries (gross - tax)."""
        total = sum(emp.net_salary for emp in self.employees.values())
        print(f"Total Net Salary to be paid to all employees: RWF {total:.2f}")
        return total
