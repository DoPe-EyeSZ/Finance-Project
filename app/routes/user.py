from flask import Blueprint, redirect, url_for, render_template, request, session, flash, jsonify
from app.models import User, Expenses, Entry, Transaction, Exp_Snap
from app import helper
import os
from app import db
import time

user = Blueprint("user", __name__, template_folder="templates", static_folder="static.style.css")


@user.route("/")
@user.route("/welcome")
def welcome():
    return render_template("welcome.html")

@user.route("/home")
def home():
    return render_template("home.html")


@user.route("/admin")        #Admin page
def admin():
    if "user_id" in session:
        user = helper.get_user(session["user_id"])
        if user.email == os.getenv("my_email"):

            info = []
            for user in User.query.all():
                user_expense = Expenses.query.filter_by(user_id = user.id).all()
                user_entry = Entry.query.filter_by(user_id = user.id).all()
                user_snapshots = Exp_Snap.query.filter_by(user_id = user.id).all()
                user_spending = Transaction.query.filter_by(user_id = user.id).all()

                info.append({"User": user, "Expenses": user_expense, "Entry": user_entry, "Snapshot": user_snapshots, "Spending": user_spending})

            return render_template("admin.html", info = info)

        else:
            return redirect(url_for("user.home"))
    
    else:
        return redirect(url_for("user.login"))


@user.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":    #Executes after login

        inputted_email = request.form["email"]      #Stores inputted pw and email 
        inputted_pw = request.form["pw"]       
        user = User.query.filter_by(email = inputted_email).first()      #Searches for user with inputted email
        


        if user:      #Checks if user exists
            if inputted_pw == user.pw:      #Login Successful

                session["user_id"] = user.id     #Save user ID to session
                session["name"] = user.name
                return redirect(url_for("user.home"))
            
            else:     #Email exist but name!=pw

                flash("Incorrect email or password.", "error")
                return render_template("login.html")  
            
        else:     #Email does not exist

            flash("Oops, Email does not exist.", "error")
            return redirect(url_for("user.sign_up"))

    else:       #User went to login page unconventionally
        if "user_id" in session:
            return redirect(url_for("user.home"))
        else:
            return render_template("login.html")



@user.route("/logout")
def logout():
    if "user_id" in session:
        flash("You've successfully logged out", "info")
    else:
        flash("You're not logged in", "info")
    
    session.clear()     #Deletes user ID and name from session
    
    return redirect(url_for("user.login"))



@user.route("/signup", methods = ["POST", "GET"])   
def sign_up():

    if request.method == "POST":        #User submits signup form

        inputted_email = request.form["email"]        #Stores inputted email, pw, and name
        inputted_pw = request.form["pw"]
        inputted_name = request.form["name"]
        existing_user = User.query.filter_by(email = inputted_email).first()        #Checks to see if email is already used

        if existing_user:        #Email already exists
            flash("Oops! Email already exists.", "error")
            return render_template("signup.html")
        
        else:        #Email does not exist, so new user "row" is created
            usr = User(inputted_email, inputted_pw, inputted_name)
            db.session.add(usr)
            db.session.commit()
            
            session["user_id"] = usr.id

        
            return redirect(url_for("user.home"))
        
    else:        #User just clicks on signup button
        return render_template("signup.html")


@user.route("/delete")
def delete():        #Deletes User account from DB
    if "user_id" in session:
        user = helper.get_user(session["user_id"])

        user_expense = Expenses.query.filter_by(user_id = session["user_id"]).delete()

        user_entry = Entry.query.filter_by(user_id = session["user_id"]).delete()

        user_spending = Transaction.query.filter_by(user_id = session["user_id"]).delete()

        user_snapshot = Exp_Snap.query.filter_by(user_id = session["user_id"]).delete()

        db.session.delete(user)
        db.session.commit()
        flash("Account was deleted successfully", "info")
    else:
        flash("Must log in to delete account.", "error")
       
    return redirect(url_for("user.logout"))



@user.route("/summary", methods=["GET"])
def summary():
    if "user_id" in session:

        #Gathering raw data (earning, spending, credit balance, deposits)

        expense_data = {}       #Store raw data from snapshots
        accumulated_expense_data = {"Balance": 0.0, 
                                    "Earnings": 0.0, 
                                    "Deposits": 0.0, 
                                    "Spendings": 0.0, 
                                    "Savings": 0.0, 
                                    "Credit_Balance": 0.0}
        
        #Grab  important information
        snaps = Exp_Snap.query.filter_by(user_id = session["user_id"]).all()
        deposits = Transaction.query.filter_by(user_id = session["user_id"], deposit_status = True).all()


        for snap in snaps:
            earnings = float(snap.expense_earnings)
            spending = float(snap.total_spending)
            credit_balance = float(snap.credit_balance)
            
            #Adding all data across all snapshots for ONE expense
            if snap.expense_id not in expense_data:
                expense_data[snap.expense_id] = {}
                
            expense_dict = expense_data[snap.expense_id]       #Shortening code for readability
            expense_dict["earnings"] = expense_dict.get("earnings", 0.0) + earnings
            expense_dict["spending"] = expense_dict.get("spending", 0.0) + spending
            expense_dict["credit_balance"] = expense_dict.get("credit_balance", 0.0) + credit_balance

            #Adding data to accumulated_expense_data
            accumulated_expense_data["Earnings"] += earnings
            accumulated_expense_data["Spendings"] += spending
            accumulated_expense_data["Credit_Balance"] += credit_balance
            

        for deposit in deposits:
            deposit_amount = deposit.amount
            expense_dict = expense_data[deposit.expense_id]
            expense_dict["deposits"] = expense_dict.get("deposits", 0.0) + deposit_amount

            #Adding deposit to accumulated_expense_data
            accumulated_expense_data["Deposits"] += deposit_amount


        #Deriving total balance and savings data
        for expense_id in expense_data:
            expense_dict = expense_data[expense_id]

            #Calculating balance and savings
            balance = expense_dict.get("earnings", 0.0) + expense_dict.get("deposits", 0.0)
            savings = balance - expense_dict.get("spending", 0.0)

            expense_dict["balance"] = balance
            expense_dict["savings"] = savings

            #Adding total balance and savings to accumulated_expense_data
            accumulated_expense_data["Balance"] += balance
            accumulated_expense_data["Savings"] += savings


        #Rounding final data values
        for data in accumulated_expense_data:
            accumulated_expense_data[data] = round(accumulated_expense_data[data], 2)

        for expense_id in expense_data:
            expense_dict = expense_data[expense_id]
            for key, value in expense_dict.items():
                if isinstance(value, (int, float)):
                    expense_dict[key] = round(value, 2)

                
        #Separating expenses, finalizing totals
        active_expenses = {}
        inactive_expenses = {}
        expenses = Expenses.query.filter_by(user_id = session["user_id"]).all()

        for expense in expenses:        #Finalizing totals
            expense_dict = expense_data[expense.id]
            expense_dict["name"] = expense.name     #Adding name

            expense.earnings = float(round(expense_dict.get("earnings", 0.0), 2))
            expense.spendings = float(round(expense_dict.get("spending", 0.0), 2))
            expense.transferred = float(round(expense_dict.get("deposits", 0.0), 2))
            expense.balance = float(round(expense_dict.get("balance", 0.0), 2))
            expense.credit_balance = float(round(expense_dict.get("credit_balance", 0.0), 2))
            expense.savings = float(round(expense_dict.get("savings", 0.0), 2))

            if expense.status:      #Separating expenses
                active_expenses[expense.id] = expense_dict
            else:
                inactive_expenses[expense.id] = expense_dict

        
        


        #Used for displaying all spending data
        spending = Transaction.query.filter_by(user_id = session["user_id"], deposit_status = False).all()

        db.session.commit()
        
        return render_template("summary.html", user = helper.get_user(session["user_id"]), 
                               active_expenses = active_expenses, inactive_expenses = inactive_expenses, 
                               lifetime_stats = accumulated_expense_data, spending = spending, 
                               expense_data = expense_data, deposits = deposits)
    

    else:
        return render_template("login.html")


    

@user.route("/profile", methods = ["GET"])
def profile():
    if helper.check_login():
        user = User.query.filter_by(id = session["user_id"]).first()
        entry_count = Entry.query.filter_by(user_id = session["user_id"]).count()
        return render_template("profile.html", user = user, entry_count = entry_count)
    else:
        return redirect(url_for("user.login"))
    

@user.route("/update_user")
def update_user():
    if helper.check_login():
        return redirect(url_for("user.edit_profile"))

    else:
        return redirect(url_for("user.login"))
    

@user.route("/profile/edit_profile", methods = ["POST", "GET"])
def edit_profile():
    if helper.check_login():
        user = User.query.filter_by(id = session["user_id"]).first()
        if request.method == "GET":
            return render_template("edit_profile.html", user = user)
        else:
            if request.form.get("curr_pw") == user.pw:
                new_pw = request.form.get("new_pw")
                new_name = request.form.get("new_name")
                new_email = request.form.get("new_email")

                if new_pw:
                    user.pw = new_pw

                if new_name:
                    user.name = new_name

                if new_email:
                    user.email = new_email

                db.session.commit()
                flash("Profile update was successful!", "success")
                return redirect(url_for("user.profile"))
            else:
                flash("Your password does not match, please try again.", "error")
                return redirect(url_for("user.edit_profile"))
            

    else:
        return redirect(url_for("user.login"))
    



#Used for retrieving data for plots
@user.route("/spending_income_data")
def get_spending_income_data():
    if helper.check_login():
        entries = Entry.query.filter_by(user_id = session["user_id"]).all()
        spendings = Transaction.query.filter_by(user_id = session["user_id"], credit_status = False, deposit_status = False).all()

        income_data = {}
        for entry in entries:
            if entry.date in income_data:
                income_data[entry.date] += entry.income
            else:
                income_data[entry.date] = entry.income

        sorted_income = sorted(income_data.items(), key=lambda x: x[0])
        dates_income = [item[0] for item in sorted_income]
        income_amounts = [item[1] for item in sorted_income]

        spending_data = {}
        for spending in spendings:
            if spending.date in spending_data:
                spending_data[spending.date] += spending.amount
            else:
                spending_data[spending.date] = spending.amount

        sorted_spending = sorted(spending_data.items(), key=lambda x: x[0])
        dates_spending = [item[0] for item in sorted_spending]
        spending_amounts = [item[1] for item in sorted_spending]
    


        data = {
            "dates_income": dates_income,
            "income": income_amounts,
            "dates_spending": dates_spending,
            "spending": spending_amounts
        }


        return jsonify(data)
    
    else:
        return redirect(url_for("user.login"))
    


@user.route("/all_expense_data")
def get_all_expense_data():
    if helper.check_login():
        expenses = []
        spending = []
        earnings = []
        savings = []

        all_expenses = Expenses.query.filter_by(user_id = session["user_id"]).all()

        for expense in all_expenses:
            expenses.append(expense.name)
            spending.append(round(expense.spendings, 2))
            earnings.append(round(expense.earnings, 2))
            savings.append(round(expense.savings, 2))


        data = {
            "expenses": expenses,
            "total_spent": spending,
            "total_earned": earnings,
            "total_saved": savings
        }

        return jsonify(data)
    else:
        return redirect(url_for("user.login"))
    

@user.route("/save_spend_data")
def save_spend_data():
    if helper.check_login():

        expenses = Expenses.query.filter_by(user_id = session["user_id"]).all()

        total_earnings = 0
        total_spent = 0
        credit_balance = 0
        total_deposits = 0
        total_savings = 0

        for expense in expenses:
            total_earnings += expense.earnings
            total_spent += expense.spendings
            credit_balance += expense.credit_balance
            total_deposits += expense.transferred
            total_savings += expense.savings

        all_data = [total_spent, total_savings]
        data_labels = ["Total Spent", "Total Savings"]
        
        data = {
            "all_data": all_data,
            "data_labels": data_labels
        }

        return jsonify(data)
    
    else:
        return redirect(url_for("user.login"))


@user.route("/all_spend_data")
def all_spend_data():
    if helper.check_login():

        spendings = Transaction.query.filter_by(user_id = session["user_id"], credit_status = False, deposit_status = False).all()

        expense_totals = {}

        for spending in spendings:
            if spending.expense_id in expense_totals:
                expense_totals[spending.expense_id] += spending.amount
            else:
                expense_totals[spending.expense_id] = spending.amount

        expenses = Expenses.query.filter(Expenses.id.in_(list(expense_totals.keys()))).all()

        # dict{expense's id: expense_name}
        expense_lookup = {}
        for expense in expenses:
            expense_lookup[expense.id] = expense.name
        
        final_data = {}

        for expense_id, amount in expense_totals.items():
            final_data[expense_lookup[expense_id]] = amount


        data = {
            "expense_name": list(final_data.keys()),
            "total": list(final_data.values())
        }
        

        return jsonify(data)

    else:
        return(redirect(url_for("user.login")))
    


@user.route("/savings_data")
def savings_data():
    if helper.check_login():
        entries = Entry.query.filter_by(user_id = session["user_id"]).all()
        spendings = Transaction.query.filter_by(user_id = session["user_id"], credit_status = False, deposit_status = False).all()

        #{entryid: spending amount}
        spending_data = {}
        for spending in spendings:
            if spending.entry_id in spending_data:
                spending_data[spending.entry_id] += spending.amount
            else:
                spending_data[spending.entry_id] = spending.amount


        #{date: income amount}
        income_data = {}
        for entry in entries:
            if entry.date in income_data:
                income_data[entry.date][0] += entry.income
            else:
                income_data[entry.date] = [entry.income, entry.id]


        #sort income amount
        sorted_income = sorted(income_data.items(), key=lambda x: x[0])     #(date, [income, entryid])
        dates = [item[0] for item in sorted_income]


        entry_income = {}       #{entry id: income amount}
        for item in sorted_income:
            id = item[1][1]
            income = item[1][0]
            entry_income[id] = income

        income_spending = {}        #{income: spending}
        for entry_id in entry_income:
            income = entry_income[entry_id]
            income_spending[income] = round(spending_data[entry_id], 2)

        #savings sorted
        saving_data = [round(income - spending, 2) for income, spending in income_spending.items()]

        data = {
            "saving_data": saving_data,
            "dates": dates
        }

        

        return jsonify(data)
    else:
        return redirect(url_for("user.login"))




@user.route("/charts", methods = ["POST", "GET"])
def charts():
    if helper.check_login():
        if request.method == "POST":
            return render_template("charts.html")
        else:
            return redirect(url_for("user.summary"))
    else:
        return redirect(url_for("user.login"))

