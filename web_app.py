from flask import Flask, render_template, request, redirect, url_for, session, Response

import sqlite3
import csv
import io
import os


from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dev-secret-key"
)
app.config["SESSION_PERMANENT"] = False


# --------------------------------------------------
# DATABASE SETUP
# --------------------------------------------------

def create_database():
    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            error = "Username and password are required."

        elif len(password) < 6:
            error = "Password must be at least 6 characters."

        else:
            hashed_password = generate_password_hash(password)

            connection = sqlite3.connect("finance.db")
            cursor = connection.cursor()

            try:
                cursor.execute("""
                    INSERT INTO users (username, password)
                    VALUES (?, ?)
                """, (
                    username,
                    hashed_password
                ))

                connection.commit()
                connection.close()

                return redirect(url_for("login"))

            except sqlite3.IntegrityError:
                connection.close()
                error = "That username already exists."

    return render_template(
        "register.html",
        error=error
    )


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        connection = sqlite3.connect("finance.db")
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, username, password
            FROM users
            WHERE username = ?
        """, (username,))

        user = cursor.fetchone()

        connection.close()

        if user and check_password_hash(user[2], password):
            session.permanent = False

            session["user_id"] = user[0]
            session["username"] = user[1]

            return redirect(url_for("home"))

        error = "Invalid username or password."

    return render_template(
        "login.html",
        error=error
    )


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():
    session.clear()

    return redirect(url_for("login"))


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Search / filter values
    search = request.args.get("search", "").strip()
    transaction_type = request.args.get("type", "").strip()
    category_filter = request.args.get("category", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    # Pagination
    page = request.args.get("page", 1, type=int)

    if page < 1:
        page = 1

    per_page = 10

    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()


    # --------------------------------------------------
    # TOTAL INCOME
    # --------------------------------------------------

    cursor.execute("""
        SELECT SUM(amount)
        FROM transactions
        WHERE user_id = ?
        AND type = 'income'
    """, (user_id,))

    total_income = cursor.fetchone()[0] or 0


    # --------------------------------------------------
    # TOTAL EXPENSES
    # --------------------------------------------------

    cursor.execute("""
        SELECT SUM(amount)
        FROM transactions
        WHERE user_id = ?
        AND type = 'expense'
    """, (user_id,))

    total_expense = cursor.fetchone()[0] or 0


    balance = total_income - total_expense


    # --------------------------------------------------
    # BUILD FILTERED TRANSACTION QUERY
    # --------------------------------------------------

    conditions = [
        "user_id = ?"
    ]

    parameters = [
        user_id
    ]


    # Search
    if search:
        conditions.append("""
            (
                LOWER(category) LIKE LOWER(?)
                OR LOWER(description) LIKE LOWER(?)
            )
        """)

        search_value = f"%{search}%"

        parameters.extend([
            search_value,
            search_value
        ])


    # Type
    if transaction_type:
        conditions.append(
            "type = ?"
        )

        parameters.append(
            transaction_type
        )


    # Category
    if category_filter:
        conditions.append(
            "LOWER(TRIM(category)) = LOWER(TRIM(?))"
        )

        parameters.append(
            category_filter
        )


    # Start date
    if start_date:
        conditions.append(
            "date(timestamp) >= date(?)"
        )

        parameters.append(
            start_date
        )


    # End date
    if end_date:
        conditions.append(
            "date(timestamp) <= date(?)"
        )

        parameters.append(
            end_date
        )


    where_clause = " AND ".join(conditions)


    # --------------------------------------------------
    # COUNT FILTERED TRANSACTIONS
    # --------------------------------------------------

    cursor.execute(
        f"""
        SELECT COUNT(*)
        FROM transactions
        WHERE {where_clause}
        """,
        parameters
    )

    total_transactions = cursor.fetchone()[0]


    total_pages = max(
        1,
        (total_transactions + per_page - 1) // per_page
    )


    if page > total_pages:
        page = total_pages


    offset = (page - 1) * per_page


    # --------------------------------------------------
    # TRANSACTIONS FOR CURRENT PAGE
    # --------------------------------------------------

    cursor.execute(
        f"""
        SELECT
            id,
            type,
            amount,
            category,
            description,
            timestamp

        FROM transactions

        WHERE {where_clause}

        ORDER BY timestamp DESC, id DESC

        LIMIT ?
        OFFSET ?
        """,
        parameters + [
            per_page,
            offset
        ]
    )

    transactions = cursor.fetchall()


    # --------------------------------------------------
    # CATEGORY FILTER OPTIONS
    # --------------------------------------------------

    cursor.execute("""
        SELECT MIN(TRIM(category))

        FROM transactions

        WHERE user_id = ?
        AND TRIM(category) != ''

        GROUP BY LOWER(TRIM(category))

        ORDER BY LOWER(TRIM(category))
    """, (user_id,))

    categories = [
        row[0]
        for row in cursor.fetchall()
    ]


    # --------------------------------------------------
    # SPENDING BY CATEGORY CHART
    # --------------------------------------------------

    cursor.execute("""
        SELECT
            LOWER(TRIM(category)),
            SUM(amount)

        FROM transactions

        WHERE user_id = ?
        AND type = 'expense'

        GROUP BY LOWER(TRIM(category))

        ORDER BY SUM(amount) DESC
    """, (user_id,))

    category_data = cursor.fetchall()


    category_labels = [
        row[0].title()
        for row in category_data
    ]


    category_values = [
        row[1]
        for row in category_data
    ]


    # --------------------------------------------------
    # MONTHLY INCOME VS EXPENSES
    # --------------------------------------------------

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

        WHERE user_id = ?

        GROUP BY month

        ORDER BY month
    """, (user_id,))

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
        selected_category=category_filter,

        start_date=start_date,
        end_date=end_date,

        username=session["username"],

        current_page=page,
        total_pages=total_pages,
        total_transactions=total_transactions
    )

@app.route("/download")
def download_statement():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    search = request.args.get("search", "").strip()
    transaction_type = request.args.get("type", "").strip()
    category_filter = request.args.get("category", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    conditions = [
        "user_id = ?"
    ]

    parameters = [
        user_id
    ]

    if search:
        conditions.append("""
            (
                LOWER(category) LIKE LOWER(?)
                OR LOWER(description) LIKE LOWER(?)
            )
        """)

        search_value = f"%{search}%"

        parameters.extend([
            search_value,
            search_value
        ])

    if transaction_type:
        conditions.append(
            "type = ?"
        )

        parameters.append(
            transaction_type
        )

    if category_filter:
        conditions.append(
            "LOWER(TRIM(category)) = LOWER(TRIM(?))"
        )

        parameters.append(
            category_filter
        )

    if start_date:
        conditions.append(
            "date(timestamp) >= date(?)"
        )

        parameters.append(
            start_date
        )

    if end_date:
        conditions.append(
            "date(timestamp) <= date(?)"
        )

        parameters.append(
            end_date
        )

    where_clause = " AND ".join(conditions)

    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()

    cursor.execute(
        f"""
        SELECT
            type,
            amount,
            category,
            description,
            timestamp

        FROM transactions

        WHERE {where_clause}

        ORDER BY timestamp DESC, id DESC
        """,
        parameters
    )

    transactions = cursor.fetchall()

    connection.close()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Date",
        "Type",
        "Amount",
        "Category",
        "Description"
    ])

    for transaction in transactions:

        writer.writerow([
            transaction[4],
            transaction[0].title(),
            f"{transaction[1]:.2f}",
            transaction[2],
            transaction[3]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=finance_statement.csv"
        }
    )


# --------------------------------------------------
# ADD TRANSACTION
# --------------------------------------------------

@app.route("/add", methods=["POST"])
def add_transaction():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

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
            user_id,
            type,
            amount,
            category,
            description
        )

        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        transaction_type,
        amount,
        category,
        description
    ))


    connection.commit()
    connection.close()


    return redirect(url_for("home"))


# --------------------------------------------------
# DELETE TRANSACTION
# --------------------------------------------------

@app.route(
    "/delete/<int:transaction_id>",
    methods=["POST"]
)
def delete_transaction(transaction_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]


    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()


    cursor.execute("""
        DELETE FROM transactions

        WHERE id = ?
        AND user_id = ?
    """, (
        transaction_id,
        user_id
    ))


    connection.commit()
    connection.close()


    return redirect(url_for("home"))


# --------------------------------------------------
# EDIT TRANSACTION
# --------------------------------------------------

@app.route(
    "/edit/<int:transaction_id>",
    methods=["GET", "POST"]
)
def edit_transaction(transaction_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]


    connection = sqlite3.connect("finance.db")
    cursor = connection.cursor()


    if request.method == "POST":
        transaction_type = request.form["type"].strip().lower()

        amount = float(
            request.form["amount"]
        )

        category = request.form["category"].strip()

        description = request.form["description"].strip()


        cursor.execute("""
            UPDATE transactions

            SET
                type = ?,
                amount = ?,
                category = ?,
                description = ?

            WHERE id = ?
            AND user_id = ?
        """, (
            transaction_type,
            amount,
            category,
            description,
            transaction_id,
            user_id
        ))


        connection.commit()
        connection.close()


        return redirect(url_for("home"))


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
        AND user_id = ?
    """, (
        transaction_id,
        user_id
    ))


    transaction = cursor.fetchone()

    connection.close()


    if transaction is None:
        return redirect(url_for("home"))


    return render_template(
        "edit_transaction.html",
        transaction=transaction
    )


# --------------------------------------------------
# START APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    create_database()

    app.run(debug=True)