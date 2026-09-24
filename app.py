
import json
from datetime import datetime


transactions = []

def save_transactions():
    with open("transactions.json", "w") as file:
        json.dump(transactions, file, indent=4)

def load_transactions():
    global transactions
    try:
        with open("transactions.json", "r") as file:
            transactions = json.load(file)
    except FileNotFoundError:
        transactions = []

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

    transaction = {
        "type": transaction_type,
        "amount": amount,
        "category": category,
        "description": description,
        "timestamp": timestamp
    }
    transactions.append(transaction)
    save_transactions()

def view_transactions():
    print("\n--- View Transactions ---")
    if not transactions:
        print("No transactions found.")
        return

    for i, transaction in enumerate(transactions, start=1):
        print(f"\nTransaction {i}:")
        print(f"Type: {transaction['type']}")
        print(f"Amount: £{transaction['amount']:.2f}")
        print(f"Category: {transaction['category']}")
        print(f"Description: {transaction['description']}")
        print(f"Timestamp: {transaction.get('timestamp','Unknown')}")


def delete_transaction():
    print("\n--- Delete Transaction ---")
    if not transactions:
        print("No transactions found.")
        return

    view_transactions()
    while True:
        try:
            index = int(input("Enter the transaction number to delete (or 0 to cancel): "))
            if index == 0:
                print("Deletion cancelled.")
                return
            if 1 <= index <= len(transactions):
                deleted_transaction = transactions.pop(index - 1)
                save_transactions()
                print(f"Transaction {index} deleted successfully!")
                return
            else:
                print(f"Invalid transaction number. Please enter a number between 1 and {len(transactions)}.")
        except ValueError:
            print("Invalid input. Please enter a valid transaction number.") 


def view_balance():
    print("\n--- View Balance ---")
    total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    balance = total_income - total_expense

    print(f"Total Income: £{total_income:.2f}")
    print(f"Total Expense: £{total_expense:.2f}")
    print(f"Current Balance: £{balance:.2f}")



def main():
    load_transactions()
    print("=== Personal Finance Tracker ===")
    while True:
        print("\n1. Add Transaction")
        print("2. View Transactions")
        print("3. View Balance")
        print("4. Delete Transaction")
        print("5. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            add_transaction()
        elif choice == "2":
            view_transactions()
        elif choice == "3":
            view_balance()
        elif choice == "4":
            delete_transaction()
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
    
