import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from database import get_db, init_db
from models import User
import pandas as pd

app = Flask(__name__)
app.secret_key = os.urandom(24)

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

with app.app_context():
    init_db()

# ─── Auth ──────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        existing = User.get_by_email(email)
        if existing:
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        User.create(name, email, hashed)
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.get_by_email(email)
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ─── Dashboard ─────────────────────────────────────────

@app.route("/")
@login_required
def dashboard():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC",
        (current_user.id,)
    ).fetchall()
    conn.close()

    transactions = [dict(r) for r in rows]
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
    balance = total_income - total_expense
    recent = transactions[:5]

    category_data = {}
    if transactions:
        df = pd.DataFrame(transactions)
        expenses_df = df[df["type"] == "expense"]
        if not expenses_df.empty:
            grouped = expenses_df.groupby("category")["amount"].sum()
            category_data = grouped.to_dict()

    return render_template("dashboard.html",
        balance=balance,
        total_income=total_income,
        total_expense=total_expense,
        recent=recent,
        category_data=category_data
    )


# ─── Transactions ──────────────────────────────────────

@app.route("/transactions")
@login_required
def transactions():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC",
        (current_user.id,)
    ).fetchall()
    conn.close()
    return render_template("transactions.html", transactions=[dict(r) for r in rows])


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    if request.method == "POST":
        t_type = request.form["type"]
        category = request.form["category"]
        amount = float(request.form["amount"])
        date = request.form["date"]
        note = request.form.get("note", "")

        conn = get_db()
        conn.execute(
            "INSERT INTO transactions (user_id, type, category, amount, date, note) VALUES (?, ?, ?, ?, ?, ?)",
            (current_user.id, t_type, category, amount, date, note)
        )
        conn.commit()
        conn.close()
        flash("Transaction added!", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_transaction.html")


@app.route("/delete/<int:transaction_id>")
@login_required
def delete_transaction(transaction_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM transactions WHERE id = ? AND user_id = ?",
        (transaction_id, current_user.id)
    )
    conn.commit()
    conn.close()
    flash("Transaction deleted.", "info")
    return redirect(url_for("transactions"))


# ─── Reports ───────────────────────────────────────────

@app.route("/reports")
@login_required
def reports():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY date ASC",
        (current_user.id,)
    ).fetchall()
    conn.close()

    transactions = [dict(r) for r in rows]
    monthly_data = {}
    insights = []

    if transactions:
        df = pd.DataFrame(transactions)
        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.strftime("%Y-%m")

        monthly = df.groupby(["month", "type"])["amount"].sum().unstack(fill_value=0)
        for month in monthly.index:
            monthly_data[month] = {
                "income": float(monthly.loc[month].get("income", 0)),
                "expense": float(monthly.loc[month].get("expense", 0))
            }

        expenses_df = df[df["type"] == "expense"]
        if not expenses_df.empty:
            top_category = expenses_df.groupby("category")["amount"].sum().idxmax()
            top_amount = expenses_df.groupby("category")["amount"].sum().max()
            insights.append(f"Your highest spending is on {top_category} (${top_amount:.2f})")

            avg_expense = expenses_df["amount"].mean()
            insights.append(f"Your average transaction expense is ${avg_expense:.2f}")

            monthly_expense = expenses_df.groupby("month")["amount"].sum()
            if len(monthly_expense) > 1:
                trend = "increasing" if monthly_expense.iloc[-1] > monthly_expense.iloc[-2] else "decreasing"
                insights.append(f"Your spending is {trend} compared to last month")

    return render_template("reports.html",
        monthly_data=monthly_data,
        insights=insights
    )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)