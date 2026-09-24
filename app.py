
import sqlite3
from datetime import datetime

transactions = []  # Global variable to store transactions

def create_database():
    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.commit()
    connection.close()


def load_transactions():
    global transactions
    transactions = []
    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM transactions")
    rows = cursor.fetchall()
    for row in rows:
        transaction = {
            "id": row[0],
            "type": row[1],
            "amount": row[2],
            "category": row[3],
            "description": row[4],
            "timestamp": row[5]
        }
        transactions.append(transaction)
    connection.close()

def add_transaction():
    print("\n--- Add Transaction ---")

    transaction_type = input("Enter transaction type (income/expense): ").strip().lower()
    while transaction_type not in ["income", "expense"]:
        print("Invalid transaction type. Please enter 'income' or 'expense'.")
        transaction_type = input("Enter transaction type (income/expense): ").strip().lower()
    
    while True:
        try:
            amount = float(input("Enter amount (£): "))
            if amount <= 0:
                print("Amount must be greater than zero. Please try again.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid number for the amount.")

    category = input("Enter category: ").strip()
    description = input("Enter description: ").strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")   

    print("\nTransaction added successfully!")
    print(f"Type: {transaction_type}")
    print(f"Amount: £{amount:.2f}")
    print(f"Category: {category}")
    print(f"Description: {description}")
    print(f"Timestamp: {timestamp}")

    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO transactions (type, amount, category, description, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (transaction_type, amount, category, description, timestamp))
    connection.commit()
    connection.close()
    load_transactions()  # Reload transactions after adding a new one



def view_transactions():
    print("\n--- View Transactions ---")
    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM transactions")
    rows = cursor.fetchall()
    connection.close()

    if not rows:
        print("No transactions found.")
        return

    for i, row in enumerate(rows, start=1):
        print(f"\nTransaction {i}:")
        print(f"Type: {row[1]}")
        print(f"Amount: £{row[2]:.2f}")
        print(f"Category: {row[3]}")
        print(f"Description: {row[4]}")
        print(f"Timestamp: {row[5]}")


def delete_transaction():
    print("\n--- Delete Transaction ---")
    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM transactions")
    rows = cursor.fetchall()
    connection.close()

    if not rows:
        print("No transactions found.")
        return

    view_transactions()
    while True:
        try:
            index = int(input("Enter the transaction number to delete (or 0 to cancel): "))
            if index == 0:
                print("Deletion cancelled.")
                return
            if 1 <= index <= len(rows):
                transaction_id = rows[index - 1][0]
                connection = sqlite3.connect("finance.db")
                cursor = connection.cursor()

                cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
                connection.commit()
                connection.close()
                load_transactions()  # Reload transactions after deletion
                print(f"Transaction {index} deleted successfully!")
                return
            else:
                print(f"Invalid transaction number. Please enter a number between 1 and {len(rows)}.")
        except ValueError:
            print("Invalid input. Please enter a valid transaction number.") 


def view_balance():
    print("\n--- View Balance ---")

    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'income'")
    total_income = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'expense'")
    total_expense = cursor.fetchone()[0] or 0

    balance = total_income - total_expense

    print(f"Total Income: £{total_income:.2f}")
    print(f"Total Expense: £{total_expense:.2f}")
    print(f"Current Balance: £{balance:.2f}")

    connection.close()

    if total_income is None:
        total_income = 0
    if total_expense is None:
        total_expense = 0
    balance = total_income - total_expense
    print(f"Total Income: £{total_income:.2f}")
    print(f"Total Expense: £{total_expense:.2f}")
    print(f"Current Balance: £{balance:.2f}")

def view_transactions_by_category():
    print("\n--- View Transactions by Category ---")

    category = input("Enter category to filter by: ").strip().lower()

    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM transactions
        WHERE LOWER(TRIM(category)) = LOWER(TRIM(?))
    """, (category,))

    rows = cursor.fetchall()
    connection.close()

    if not rows:
        print(f"No transactions found for category '{category}'.")
        return

    for i, row in enumerate(rows, start=1):
        print(f"\nTransaction {i}:")
        print(f"Type: {row[1]}")
        print(f"Amount: £{row[2]:.2f}")
        print(f"Category: {row[3]}")
        print(f"Description: {row[4]}")
        print(f"Timestamp: {row[5]}")

def view_spending_by_category():
    print("\n--- View Spending by Category ---")

    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT LOWER(TRIM(category)), SUM(amount)
        FROM transactions
        WHERE type = 'expense'
        GROUP BY LOWER(TRIM(category))
        ORDER BY SUM(amount) DESC
    """)

    rows = cursor.fetchall()
    connection.close()

    if not rows:
        print("No expense transactions found.")
        return

    print("\nSpending by Category:")

    for category, total in rows:
        print(f"Category: {category}, Total Spending: £{total:.2f}")

def main():
    create_database()
    load_transactions()
    
    print("=== Personal Finance Tracker ===")
    while True:
        print("\n1. Add Transaction")
        print("2. View Transactions")
        print("3. View Balance")
        print("4. View Transactions by Category")
        print("5. View Spending by Category")
        print("6. Delete Transaction")
        print("7. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            add_transaction()
        elif choice == "2":
            view_transactions()
        elif choice == "3":
            view_balance()
        elif choice == "4":
            view_transactions_by_category()
        elif choice == "5":
            view_spending_by_category()
        elif choice == "6":
            delete_transaction()
        elif choice == "7":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
    
