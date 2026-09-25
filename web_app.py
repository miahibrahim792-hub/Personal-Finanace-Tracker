from flask import Flask, render_template, request, redirect, url_for
import sqlite3


app = Flask(__name__)

@app.route('/')
def home():
    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT SUM(amount) FROM transactions WHERE type = 'income'
    """)
    total_income = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT SUM(amount) FROM transactions WHERE type = 'expense'
    """)
    total_expense = cursor.fetchone()[0]

    connection.close()

    if total_income is None:
        total_income = 0
    if total_expense is None:
        total_expense = 0

    balance = total_income - total_expense

    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, type, amount, category, description, timestamp
        FROM transactions
        ORDER BY timestamp DESC, id DESC
    """)

    transactions = cursor.fetchall()
    connection.close()

    return render_template(
    "dashboard.html",
    balance=balance,
    total_income=total_income,
    total_expense=total_expense,
    transactions=transactions
)

@app.route("/add", methods=["POST"])
def add_transaction():
    transaction_type = request.form["type"].strip().lower()
    amount = float(request.form["amount"])
    category = request.form["category"].strip()
    description = request.form["description"].strip()

    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO transactions (type, amount, category, description)
        VALUES (?, ?, ?, ?)
    """, (
        transaction_type,
        amount,
        category,
        description
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))

@app.route("/delete/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):
    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM transactions WHERE id = ?",
        (transaction_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("home"))

@app.route("/edit/<int:transaction_id>", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()

    if request.method == "POST":
        transaction_type = request.form["type"].strip().lower()
        amount = float(request.form["amount"])
        category = request.form["category"].strip()
        description = request.form["description"].strip()

        cursor.execute("""
            UPDATE transactions
            SET type = ?, amount = ?, category = ?, description = ?
            WHERE id = ?
        """, (
            transaction_type,
            amount,
            category,
            description,
            transaction_id
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("home"))

    cursor.execute("""
        SELECT id, type, amount, category, description, timestamp
        FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    transaction = cursor.fetchone()
    connection.close()

    return render_template(
        "edit_transaction.html",
        transaction=transaction
    )



if __name__ == '__main__':
    app.run(debug=True)