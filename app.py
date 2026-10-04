from flask import Flask, render_template, request, redirect, url_for
from database import get_db_connection

app = Flask(__name__)


# =========================
# LOGIN
# =========================
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT * FROM admins
            WHERE username = %s AND password = %s
        """

        cursor.execute(query, (username, password))
        admin = cursor.fetchone()

        cursor.close()
        connection.close()

        if admin:
            return redirect(url_for("dashboard"))

        return "Invalid username or password"

    return render_template("login.html")


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():

    connection = get_db_connection()
    cursor = connection.cursor()

    # Total customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    # Total accounts
    cursor.execute("SELECT COUNT(*) FROM accounts")
    total_accounts = cursor.fetchone()[0]

    # Active accounts
    cursor.execute("""
        SELECT COUNT(*) FROM accounts
        WHERE status = 'Active'
    """)
    active_accounts = cursor.fetchone()[0]

    # Total transactions
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return render_template(
        "dashboard.html",
        total_customers=total_customers,
        total_accounts=total_accounts,
        active_accounts=active_accounts,
        total_transactions=total_transactions
    )


# =========================
# CUSTOMER MANAGEMENT
# =========================
@app.route("/customers", methods=["GET", "POST"])
def customers():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Add new customer
    if request.method == "POST":

        name = request.form["name"]
        mobile = request.form["mobile"]
        email = request.form["email"]
        address = request.form["address"]
        date_of_birth = request.form["date_of_birth"]

        query = """
            INSERT INTO customers
            (name, mobile, email, address, date_of_birth)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (name, mobile, email, address, date_of_birth)
        )

        connection.commit()

    # Get all customers
    cursor.execute("SELECT * FROM customers ORDER BY customer_id DESC")

    customer_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "customers.html",
        customers=customer_list
    )

# =========================
# ACCOUNT MANAGEMENT
# =========================
@app.route("/accounts", methods=["GET", "POST"])
def accounts():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Create new account
    if request.method == "POST":

        customer_id = request.form["customer_id"]
        account_type = request.form["account_type"]
        branch = request.form["branch"]
        balance = request.form["balance"]

        query = """
            INSERT INTO accounts
            (customer_id, account_type, branch, balance, status, opening_date)
            VALUES (%s, %s, %s, %s, 'Active', CURDATE())
        """

        cursor.execute(
            query,
            (customer_id, account_type, branch, balance)
        )

        connection.commit()

    # Get customers
    cursor.execute("""
        SELECT customer_id, name
        FROM customers
        ORDER BY customer_id
    """)

    customer_list = cursor.fetchall()

    # Get accounts with customer names
    cursor.execute("""
        SELECT
            accounts.account_id,
            accounts.customer_id,
            customers.name,
            accounts.account_type,
            accounts.branch,
            accounts.balance,
            accounts.status,
            accounts.opening_date
        FROM accounts
        JOIN customers
        ON accounts.customer_id = customers.customer_id
        ORDER BY accounts.account_id DESC
    """)

    account_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "accounts.html",
        customers=customer_list,
        accounts=account_list
    )
# =========================
# TRANSACTION MANAGEMENT
# =========================
@app.route("/transactions", methods=["GET", "POST"])
def transactions():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Create transaction
    if request.method == "POST":

        account_id = request.form["account_id"]
        transaction_type = request.form["transaction_type"]
        amount = float(request.form["amount"])
        description = request.form["description"]

        # Get current account balance
        cursor.execute("""
            SELECT balance
            FROM accounts
            WHERE account_id = %s
        """, (account_id,))

        account = cursor.fetchone()

        if account is None:
            cursor.close()
            connection.close()
            return "Account not found"

        current_balance = float(account["balance"])

        # Deposit
        if transaction_type == "Deposit":

            new_balance = current_balance + amount

        # Withdrawal
        elif transaction_type == "Withdrawal":

            if amount > current_balance:
                cursor.close()
                connection.close()
                return "Insufficient balance"

            new_balance = current_balance - amount

        else:
            cursor.close()
            connection.close()
            return "Invalid transaction type"

        # Insert transaction
        cursor.execute("""
            INSERT INTO transactions
            (account_id, transaction_type, amount, description)
            VALUES (%s, %s, %s, %s)
        """, (
            account_id,
            transaction_type,
            amount,
            description
        ))

        # Update account balance
        cursor.execute("""
            UPDATE accounts
            SET balance = %s
            WHERE account_id = %s
        """, (
            new_balance,
            account_id
        ))

        connection.commit()

    # Get all accounts
    cursor.execute("""
        SELECT
            accounts.account_id,
            customers.name,
            accounts.account_type,
            accounts.balance
        FROM accounts
        JOIN customers
        ON accounts.customer_id = customers.customer_id
        WHERE accounts.status = 'Active'
        ORDER BY accounts.account_id
    """)

    account_list = cursor.fetchall()

    # Get transaction history
    cursor.execute("""
        SELECT
            transactions.transaction_id,
            transactions.account_id,
            customers.name,
            transactions.transaction_type,
            transactions.amount,
            transactions.transaction_date,
            transactions.description
        FROM transactions
        JOIN accounts
        ON transactions.account_id = accounts.account_id
        JOIN customers
        ON accounts.customer_id = customers.customer_id
        ORDER BY transactions.transaction_id DESC
    """)

    transaction_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "transactions.html",
        accounts=account_list,
        transactions=transaction_list
    )
# =========================
# REPORTS
# =========================
@app.route("/reports")
def reports():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Total customers
    cursor.execute("SELECT COUNT(*) AS total FROM customers")
    total_customers = cursor.fetchone()["total"]

    # Total accounts
    cursor.execute("SELECT COUNT(*) AS total FROM accounts")
    total_accounts = cursor.fetchone()["total"]

    # Active accounts
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM accounts
        WHERE status = 'Active'
    """)
    active_accounts = cursor.fetchone()["total"]

    # Total transactions
    cursor.execute("SELECT COUNT(*) AS total FROM transactions")
    total_transactions = cursor.fetchone()["total"]

    # Total deposits
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE transaction_type = 'Deposit'
    """)
    total_deposits = cursor.fetchone()["total"]

    # Total withdrawals
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE transaction_type = 'Withdrawal'
    """)
    total_withdrawals = cursor.fetchone()["total"]

    cursor.close()
    connection.close()

    return render_template(
        "reports.html",
        total_customers=total_customers,
        total_accounts=total_accounts,
        active_accounts=active_accounts,
        total_transactions=total_transactions,
        total_deposits=total_deposits,
        total_withdrawals=total_withdrawals
    )
# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    return redirect(url_for("login"))


# =========================
# START FLASK SERVER
# =========================
if __name__ == "__main__":
    app.run(debug=True)