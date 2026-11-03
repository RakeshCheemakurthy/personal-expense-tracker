
# Personal Expense Tracker

A web-based application to manage personal income and expenses, track monthly balances, and visualize financial records.

## Features
- Add, edit, and delete transactions.
- Monthly income and expense totals.
- Automatic monthly balance calculation.
- Search and filter transactions.
- Filter by category and date.
- Expense category chart.
- Income vs. expenses chart.

## Technologies Used
- Python
- Flask
- MySQL
- Matplotlib
- HTML
- CSS

## Project Structure
```text
personal-expense-tracker/
├── app.py
├── requirements.txt
├── README.md
├── schema.sql
├── .gitignore
├── static/
└── templates/
```

## Setup on Windows

### 1. Install Python and MySQL Server.

### 2. Create the database
Run `schema.sql` in MySQL Workbench.

### 3. Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Install required packages

```powershell
python -m pip install -r requirements.txt
```

### 5. Configure database variables

```powershell
$env:DB_HOST="localhost"
$env:DB_USER="root"
$env:DB_PASSWORD="your_mysql_password"
$env:DB_NAME="expense_tracker"
```

Replace the example password with your own MySQL password. Never upload database passwords to GitHub.

### 6. Run the application

```powershell
python app.py
```

### 7. Open in browser

http://127.0.0.1:5000/

## Database
MySQL is used to store income and expense transactions.

## License
For educational and learning purposes.
