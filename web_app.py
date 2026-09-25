from flask import Flask, render_template, request, redirect, url_for
import sqlite3


app = Flask(__name__)


# -------------------------
# DATABASE SETUP
# -------------------------

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


# -------------------------
# DASHBOARD
# -------------------------

@app.route("/")
def home():

    # Search / filter values from the webpage
    search = request.args.get("search", "").strip()
    transaction_type = request.args.get("type", "").strip()
    category_filter = request.args.get("category", "").strip()

    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()


    # -------------------------
    # TOTAL INCOME
    # -------------------------

    cursor.execute("""
        SELECT SUM(amount)
        FROM transactions
        WHERE type = 'income'
    """)

    total_income = cursor.fetchone()[0] or 0


    # -------------------------
    # TOTAL EXPENSES
    # -------------------------

    cursor.execute("""
        SELECT SUM(amount)
        FROM transactions
        WHERE type = 'expense'
    """)

    total_expense = cursor.fetchone()[0] or 0


    # -------------------------
    # CURRENT BALANCE
    # -------------------------

    balance = total_income - total_expense


    # -------------------------
    # TRANSACTION SEARCH/FILTER
    # -------------------------

    query = """
        SELECT id, type, amount, category, description, timestamp
        FROM transactions
        WHERE 1 = 1
    """

    parameters = []


    # Search category or description
    if search:

        query += """
            AND (
                LOWER(category) LIKE LOWER(?)
                OR LOWER(description) LIKE LOWER(?)
            )
        """

        search_value = f"%{search}%"

        parameters.extend([
            search_value,
            search_value
        ])


    # Filter by income / expense
    if transaction_type:

        query += """
            AND type = ?
        """

        parameters.append(transaction_type)


    # Filter by category
    if category_filter:

        query += """
            AND LOWER(TRIM(category)) = LOWER(TRIM(?))
        """

        parameters.append(category_filter)


    query += """
        ORDER BY timestamp DESC, id DESC
    """


    cursor.execute(query, parameters)

    transactions = cursor.fetchall()


    # -------------------------
    # CATEGORY LIST FOR FILTER
    # -------------------------

    cursor.execute("""
        SELECT MIN(TRIM(category))
        FROM transactions
        WHERE TRIM(category) != ''
        GROUP BY LOWER(TRIM(category))
        ORDER BY LOWER(TRIM(category))
    """)

    categories = [
        row[0]
        for row in cursor.fetchall()
    ]


    # -------------------------
    # SPENDING BY CATEGORY
    # -------------------------

    cursor.execute("""
        SELECT
            LOWER(TRIM(category)),
            SUM(amount)
        FROM transactions
        WHERE type = 'expense'
        GROUP BY LOWER(TRIM(category))
        ORDER BY SUM(amount) DESC
    """)

    category_data = cursor.fetchall()


    category_labels = [
        row[0].title()
        for row in category_data
    ]


    category_values = [
        row[1]
        for row in category_data
    ]


    # -------------------------
    # MONTHLY INCOME / EXPENSES
    # -------------------------

    cursor.execute("""
        SELECT
            strftime('%Y-%m', timestamp) AS month,

            SUM(
                CASE
                    WHEN type = 'income'
                    THEN amount
                    ELSE 0
                END
            ),

            SUM(
                CASE
                    WHEN type = 'expense'
                    THEN amount
                    ELSE 0
                END
            )

        FROM transactions

        GROUP BY month

        ORDER BY month
    """)


    monthly_data = cursor.fetchall()


    month_labels = [
        row[0]
        for row in monthly_data
    ]


    monthly_income = [
        row[1]
        for row in monthly_data
    ]


    monthly_expenses = [
        row[2]
        for row in monthly_data
    ]


    connection.close()


    # -------------------------
    # SEND DATA TO HTML
    # -------------------------

    return render_template(
        "dashboard.html",

        balance=balance,
        total_income=total_income,
        total_expense=total_expense,

        transactions=transactions,

        category_labels=category_labels,
        category_values=category_values,

        month_labels=month_labels,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,

        categories=categories,

        search=search,
        selected_type=transaction_type,
        selected_category=category_filter
    )


# -------------------------
# ADD TRANSACTION
# -------------------------

@app.route("/add", methods=["POST"])
def add_transaction():

    transaction_type = request.form["type"].strip().lower()

    amount = float(
        request.form["amount"]
    )

    category = request.form["category"].strip()

    description = request.form["description"].strip()


    connection = sqlite3.connect("finance.db")

    cursor = connection.cursor()


    cursor.execute("""
        INSERT INTO transactions (
            type,
            amount,
            category,
            description
        )

        VALUES (?, ?, ?, ?)
    """, (

        transaction_type,
        amount,
        category,
        description

    ))


    connection.commit()

    connection.close()


    return redirect(
        url_for("home")
    )


# -------------------------
# DELETE TRANSACTION
# -------------------------

@app.route(
    "/delete/<int:transaction_id>",
    methods=["POST"]
)
def delete_transaction(transaction_id):

    connection = sqlite3.connect("finance.db")

    cursor = connection.cursor()


    cursor.execute("""
        DELETE FROM transactions
        WHERE id = ?
    """, (
        transaction_id,
    ))


    connection.commit()

    connection.close()


    return redirect(
        url_for("home")
    )


# -------------------------
# EDIT TRANSACTION
# -------------------------

@app.route(
    "/edit/<int:transaction_id>",
    methods=["GET", "POST"]
)
def edit_transaction(transaction_id):

    connection = sqlite3.connect("finance.db")

    cursor = connection.cursor()


    # Save edited transaction
    if request.method == "POST":

        transaction_type = (
            request.form["type"]
            .strip()
            .lower()
        )

        amount = float(
            request.form["amount"]
        )

        category = (
            request.form["category"]
            .strip()
        )

        description = (
            request.form["description"]
            .strip()
        )


        cursor.execute("""
            UPDATE transactions

            SET
                type = ?,
                amount = ?,
                category = ?,
                description = ?

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


        return redirect(
            url_for("home")
        )


    # Load existing transaction
    cursor.execute("""
        SELECT
            id,
            type,
            amount,
            category,
            description,
            timestamp

        FROM transactions

        WHERE id = ?
    """, (
        transaction_id,
    ))


    transaction = cursor.fetchone()

    connection.close()


    return render_template(
        "edit_transaction.html",
        transaction=transaction
    )


# -------------------------
# START APPLICATION
# -------------------------

if __name__ == "__main__":

    create_database()

    app.run(debug=True)