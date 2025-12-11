from payroll import Payroll
from models.fulltime import FullTimeEmployee
from models.contract import ContractEmployee
from models.intern import Intern


def main():
    payroll = Payroll()
      

    while True:
        print("\n--- Employee Payroll Tracker ---")
        print("1. Add Employee")
        print("2. Update Salary")
        print("3. Update Bonus")
        print("4. Generate All Payslips")
        print("5. Summary Report")
        print("6. Search Employee by ID")
        print("7. Company Payroll Overview")
    
        print("0. Exit")

        choice = input("Enter your choice: ").strip()
        if choice == "1":
            add_employee_cli(payroll)
        elif choice == "2":
            update_salary_cli(payroll)
        elif choice == "3":
            update_bonus_cli(payroll)
        elif choice == "4":
            payroll.generate_all_payslips()
        elif choice == "5":
            payroll.summary_report()
        elif choice == "6":
            emp_id = int(input("Enter employee ID: "))
            emp = payroll.get_employee(emp_id)
            if emp:
                emp.generate_payslip()
            else:
                print("Employee not found")
                
        elif choice == "7":  
            print("\n--- Company Payroll Overview ---")
            payroll.total_gross_salary()
            payroll.total_tax()
            payroll.total_net_salary()

        elif choice == "0":
            print("Exiting Payroll Tracker")
            break
        else:
            print("Invalid choice. Try again.")

def add_employee_cli(payroll):
    emp_type = input("Enter type (FullTime/Contract/Intern): ").strip().lower()
    name = input("Name: ").strip()
    dept = input("Department: ").strip()
    pos = input("Position: ").strip()


    try:
        if emp_type == "fulltime":
            salary = float(input("Monthly Salary: "))
            bonus = input("Bonus: ")  
            bonus = float(bonus) if bonus else 0
            payroll.add_employee(FullTimeEmployee(name, dept, pos, salary, bonus))

        elif emp_type == "contract":
            hours = float(input("Hours Worked: "))
            rate = float(input("Hourly Rate: "))
            bonus = input("Bonus: ")
            bonus = float(bonus) if bonus else 0
            payroll.add_employee(ContractEmployee(name, dept, pos, hours, rate, bonus))

        elif emp_type == "intern":
            stipend = float(input("Stipend: "))
            payroll.add_employee(Intern(name, dept, pos, stipend))
        else:
            print("Invalid employee type!")

    except ValueError as ve:
        print(f"Input error: {ve}")

def update_salary_cli(payroll):
    emp_id = int(input("Enter employee ID: "))
    new_salary = float(input("Enter new salary: "))
    payroll.update_salary(emp_id, new_salary)

def update_bonus_cli(payroll):
    emp_id = int(input("Enter employee ID: "))
    new_bonus = float(input("Enter new bonus: "))
    payroll.update_bonus(emp_id, new_bonus)

if __name__ == "__main__":
    main()
