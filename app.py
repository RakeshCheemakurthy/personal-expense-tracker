
import os
import io
from decimal import Decimal, InvalidOperation
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, Response
)
import mysql.connector


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me")

CATEGORIES = [
    "Salary", "Food", "Travel", "Shopping",
    "Bills", "Education", "Health", "Other"
]


# ---------------- DATABASE CONNECTION ----------------

def db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "expense_tracker")
    )


def run(sql, params=(), one=False):
    connection = db()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        result = cursor.fetchone() if one else cursor.fetchall()
        connection.commit()
        cursor.close()
        return result
    finally:
        connection.close()


# ---------------- HELPER FUNCTIONS ----------------

def valid_month(value):
    try:
        year, month_number = map(int, value.split("-"))
        if not (2000 <= year <= 2100 and 1 <= month_number <= 12):
            raise ValueError
        return value
    except (ValueError, AttributeError):
        return date.today().strftime("%Y-%m")


def month_params(month):
    first_day = f"{month}-01"
    return first_day, first_day


# ---------------- MAIN DASHBOARD ----------------

@app.route("/")
def index():
    month = valid_month(
        request.args.get("month", date.today().strftime("%Y-%m"))
    )

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "")
    transaction_type = request.args.get("transaction_type", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    if category not in CATEGORIES:
        category = ""

    if transaction_type not in ("income", "expense"):
        transaction_type = ""

    conditions = [
        "transaction_date >= %s",
        "transaction_date < DATE_ADD(%s, INTERVAL 1 MONTH)"
    ]
    params = list(month_params(month))

    if search:
        conditions.append("(title LIKE %s OR note LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])

    if category:
        conditions.append("category = %s")
        params.append(category)

    if transaction_type:
        conditions.append("transaction_type = %s")
        params.append(transaction_type)

    # Validate date range
    try:
        if start_date:
            date.fromisoformat(start_date)
        if end_date:
            date.fromisoformat(end_date)
        if start_date and end_date and start_date > end_date:
            raise ValueError
    except ValueError:
        start_date = ""
        end_date = ""
        flash("Please select a valid date range.", "error")

    if start_date:
        conditions.append("transaction_date >= %s")
        params.append(start_date)

    if end_date:
        conditions.append("transaction_date <= %s")
        params.append(end_date)

    where_sql = " AND ".join(conditions)

    transactions = run(
        f"""
        SELECT * FROM transactions
        WHERE {where_sql}
        ORDER BY transaction_date DESC, id DESC
        """,
        tuple(params)
    )

    # Monthly summary
    totals = run(
        """
        SELECT
            COALESCE(SUM(
                CASE WHEN transaction_type = 'income'
                THEN amount ELSE 0 END
            ), 0) AS income,
            COALESCE(SUM(
                CASE WHEN transaction_type = 'expense'
                THEN amount ELSE 0 END
            ), 0) AS expenses
        FROM transactions
        WHERE transaction_date >= %s
          AND transaction_date < DATE_ADD(%s, INTERVAL 1 MONTH)
        """,
        month_params(month),
        one=True
    )

    totals["balance"] = (
        Decimal(str(totals["income"]))
        - Decimal(str(totals["expenses"]))
    )

    return render_template(
        "index.html",
        transactions=transactions,
        totals=totals,
        month=month,
        search=search,
        category=category,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        categories=CATEGORIES
    )


# ---------------- ADD TRANSACTION ----------------

@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    kind = request.form.get("transaction_type", "")
    category = request.form.get("category", "")
    raw_amount = request.form.get("amount", "")
    transaction_date = request.form.get("transaction_date", "")
    note = request.form.get("note", "").strip()

    try:
        amount = Decimal(raw_amount)

        if (
            not title
            or kind not in ("income", "expense")
            or category not in CATEGORIES
            or amount <= 0
        ):
            raise ValueError

        date.fromisoformat(transaction_date)

    except (InvalidOperation, ValueError):
        flash("Please enter valid transaction details.", "error")
        return redirect(url_for("index"))

    run(
        """
        INSERT INTO transactions
        (title, transaction_type, category, amount,
         transaction_date, note)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (title, kind, category, amount, transaction_date, note)
    )

    flash("Transaction added successfully.")
    return redirect(url_for("index", month=transaction_date[:7]))


# ---------------- EDIT TRANSACTION ----------------

@app.route("/edit/<int:tid>", methods=["GET", "POST"])
def edit(tid):
    item = run(
        "SELECT * FROM transactions WHERE id = %s",
        (tid,),
        one=True
    )

    if not item:
        flash("Transaction not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        kind = request.form.get("transaction_type", "")
        category = request.form.get("category", "")
        raw_amount = request.form.get("amount", "")
        transaction_date = request.form.get("transaction_date", "")
        note = request.form.get("note", "").strip()

        try:
            amount = Decimal(raw_amount)

            if (
                not title
                or kind not in ("income", "expense")
                or category not in CATEGORIES
                or amount <= 0
            ):
                raise ValueError

            date.fromisoformat(transaction_date)

        except (InvalidOperation, ValueError):
            flash("Please enter valid transaction details.", "error")
            return redirect(url_for("edit", tid=tid))

        run(
            """
            UPDATE transactions
            SET title = %s,
                transaction_type = %s,
                category = %s,
                amount = %s,
                transaction_date = %s,
                note = %s
            WHERE id = %s
            """,
            (
                title, kind, category, amount,
                transaction_date, note, tid
            )
        )

        flash("Transaction updated.")
        return redirect(url_for("index", month=transaction_date[:7]))

    return render_template("edit.html", item=item)


# ---------------- DELETE TRANSACTION ----------------

@app.route("/delete/<int:tid>", methods=["POST"])
def delete(tid):
    run("DELETE FROM transactions WHERE id = %s", (tid,))
    flash("Transaction deleted.")
    return redirect(url_for("index"))


# ---------------- EXPENSE CATEGORY CHART ----------------

@app.route("/expense-chart")
def expense_chart():
    month = valid_month(
        request.args.get("month", date.today().strftime("%Y-%m"))
    )

    rows = run(
        """
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE transaction_type = 'expense'
          AND transaction_date >= %s
          AND transaction_date < DATE_ADD(%s, INTERVAL 1 MONTH)
        GROUP BY category
        ORDER BY total DESC
        """,
        month_params(month)
    )

    fig, ax = plt.subplots(figsize=(6, 4))

    if rows:
        labels = [row["category"] for row in rows]
        values = [float(row["total"]) for row in rows]

        ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops={"width": 0.45}
        )
        ax.set_title("Expenses by Category")
    else:
        ax.text(
            0.5, 0.5, "No expense data available",
            ha="center", va="center"
        )
        ax.axis("off")

    fig.tight_layout()
    image_buffer = io.BytesIO()
    fig.savefig(image_buffer, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    image_buffer.seek(0)

    return Response(image_buffer.getvalue(), mimetype="image/png")


# ---------------- INCOME VS EXPENSE CHART ----------------

@app.route("/income-expense-chart")
def income_expense_chart():
    month = valid_month(
        request.args.get("month", date.today().strftime("%Y-%m"))
    )

    totals = run(
        """
        SELECT
            COALESCE(SUM(
                CASE WHEN transaction_type = 'income'
                THEN amount ELSE 0 END
            ), 0) AS income,
            COALESCE(SUM(
                CASE WHEN transaction_type = 'expense'
                THEN amount ELSE 0 END
            ), 0) AS expenses
        FROM transactions
        WHERE transaction_date >= %s
          AND transaction_date < DATE_ADD(%s, INTERVAL 1 MONTH)
        """,
        month_params(month),
        one=True
    )

    labels = ["Income", "Expenses"]
    values = [
        float(totals["income"]),
        float(totals["expenses"])
    ]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, values)
    ax.set_title("Income vs Expenses")
    ax.set_ylabel("Amount (₹)")
    ax.set_ylim(bottom=0)
    ax.bar_label(bars, fmt="₹%.2f", padding=3)

    fig.tight_layout()
    image_buffer = io.BytesIO()
    fig.savefig(image_buffer, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    image_buffer.seek(0)

    return Response(image_buffer.getvalue(), mimetype="image/png")


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)
