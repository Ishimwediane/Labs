# Employee Payroll Tracker

A **console-based Python application** for managing employees, payroll, and salary operations.
Supports **Full-Time, Contract, and Intern employees**, calculates salaries automatically, generates payslips, provides summary reports, and calculates taxes and net salary. Employee IDs are assigned automatically and employees are stored in a **dictionary** for fast lookup.

---

##  Features

- **Add Employees**
  - Full-Time, Contract, or Intern
  - Automatic employee ID assignment
  - Optional bonus support

- **Update Salary and Bonus**
  - Modify an employee's salary or bonus at any time

- **Generate Payslips**
  - View individual or all employee payslips
  - Shows base salary/stipend, bonus, tax, and total salary

- **Summary Report**
  - Lists all employees with total salary and tax information

- **Search Employee**
  - Search by employee ID and display detailed payslip

- **Remove Employee**
  - Remove an employee from the system

- **Company Payroll Overview**
  - Total gross salary
  - Total tax deducted
  - Total net salary to be paid

---

##  Employee Types

### 1. Full-Time Employee
- Fixed monthly salary + optional bonus
- Tax applies on salary only (progressive rates)

### 2. Contract Employee
- Paid based on hours worked × hourly rate + optional bonus
- Tax applies on salary only

### 3. Intern
- Fixed stipend + optional bonus
- Tax applies only if stipend > 30,000 RWF per month

---

## Folder Structure

```
Employee-Payroll-Tracker/
│
├── main.py                 # Main program (CLI interface)
├── payroll.py              # Payroll management class
├── models/
│   ├── __init__.py
│   ├── employee.py         # Abstract base Employee class
│   ├── fulltime.py         # Full-Time Employee class
│   ├── contract.py         # Contract Employee class
│   └── intern.py           # Intern class
├── requirements.txt        # Project dependencies (optional)
└── README.md               # Project documentation
```

---

##  Installation

### 1. Clone the repository:
```bash
git clone <repo-name>
cd employee-payroll-tracker
```

### 2. Create and activate a virtual environment:
```bash
# On Linux/Mac
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies (if any):
```bash
pip install -r requirements.txt
```

---

##  Usage

### Run the application:
```bash
python main.py
```

### Main Menu:
```
---- Employee Payroll Tracker Menu ----
1. Add Employee
2. Update Salary
3. Update Bonus
4. Generate All Payslips
5. Summary Report
6. Search Employee by ID
7. Remove Employee
8. Company Payroll Overview
9. Exit
```

Follow the prompts to add employees, update salaries/bonuses, generate payslips, or view reports.

---

##  How It Works

### Adding Employees

When adding an employee, you'll be prompted for:

- **Employee Type**: FullTime, Contract, or Intern
- **Name**: Employee's full name (required)
- **Department**: Department they belong to
- **Position**: Job title or role
- **Salary Details**:
  - **Full-Time**: Monthly salary
  - **Contract**: Hourly rate and hours worked
  - **Intern**: Monthly stipend
- **Bonus** (optional): Additional compensation

### Salary Calculation

- **Full-Time Employee**: `Total = Monthly Salary + Bonus`
- **Contract Employee**: `Total = (Hours Worked × Hourly Rate) + Bonus`
- **Intern**: `Total = Stipend + Bonus` (tax-free if stipend ≤ 30,000 RWF)

### Tax Calculation (Rwanda Example)

- Progressive tax applied only to salary/stipend, **not bonus**
- Interns below 30,000 RWF are tax-exempt
- Contract and Full-Time employees always pay tax on salary

### Net Salary

```
Net Salary = Total Salary - Tax
```

---

##  Example Usage

### Adding a Full-Time Employee

```
Enter your choice: 1
Enter type (FullTime/Contract/Intern): FullTime
Name: Alice
Department: IT
Position: Developer
Monthly Salary: 500000
Bonus (press Enter to skip): 50000

✔ Employee Alice added successfully with ID: 1
```

### Generating All Payslips

```
Enter your choice: 4

========================================
          PAYROLL PAYSLIPS
========================================

----------------------------------------
Employee ID: 1
Name: Alice
Type: Full-Time
Department: IT | Position: Developer
Base Salary: RWF 500,000.00
Bonus: RWF 50,000.00
Tax: RWF 72,000.00
Total Pay: RWF 478,000.00
----------------------------------------
```

### Company Payroll Overview

```
Enter your choice: 7

--- Company Payroll Overview ---
Total Gross Salary: RWF 950,000.00
Total Tax Deducted: RWF 120,000.00
Total Net Salary: RWF 830,000.00
```

---

##  Notes

- Employees are stored in a **dictionary** (`employee_id → Employee object`) for fast access
- Employee IDs are generated **sequentially** starting from 1
- Bonus is **optional** (defaults to 0)
- **Contract employees'** salary = `hours_worked × hourly_rate + bonus`
- **Full-time employees'** salary = `monthly_salary + bonus`
- **Interns'** salary = `stipend + bonus`; tax applied if `stipend > 30,000 RWF`
- Monetary values are displayed in **RWF** with two decimal places

---

##  Requirements

- **Python 3.6** or higher
- No external dependencies (uses Python standard library)

---

##  Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

##  Future Enhancements

- [ ] Export payslips to PDF or CSV
- [ ] Database integration for persistent storage
- [ ] GUI interface (Tkinter/PyQt)
- [ ] Email payslips to employees
- [ ] Multi-currency support
- [ ] Monthly/yearly reports
- [ ] Advanced tax calculation models
- [ ] Employee attendance tracking
- [ ] Leave management system

---

##  Contact

**Questions or suggestions?**
 ishimwediane400@gmail.com

---

## Acknowledgments

- Built with **Python**
- Inspired by real-world payroll systems
- Thanks to all contributors

---

## Demo
- https://drive.google.com/file/d/1dHrpulBMSqZZ9H6AKG_VCfSylEfWU9xT/view?usp=sharing





