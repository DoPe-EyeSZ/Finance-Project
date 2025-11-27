from flask import Blueprint, redirect, url_for, render_template, request, session, flash, jsonify
from app.models import User, Expenses, Entry, Spending, Exp_Snap
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
                user_spending = Spending.query.filter_by(user_id = user.id).all()

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

                flash("Incorrect email or password.")
                return render_template("login.html")  
            
        else:     #Email does not exist

            flash("Oops, Email does not exist.", "warning")
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
            flash("Oops! Email already exists.")
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

        user_spending = Spending.query.filter_by(user_id = session["user_id"]).delete()

        user_snapshot = Exp_Snap.query.filter_by(user_id = session["user_id"]).delete()

        db.session.delete(user)
        db.session.commit()
        flash("Account was deleted successfully., info")
    else:
        flash("Must log in to delete account.")
       
    return redirect(url_for("user.logout"))



@user.route("/summary", methods=["GET"])
def summary():
    if "user_id" in session:
        active_expenses = {}
        inactive_expenses = {}
        
        snaps = Exp_Snap.query.filter_by(user_id = session["user_id"]).all()

        expenses = Expenses.query.filter_by(user_id = session["user_id"]).all()
        expenses_ID = {expense.id: expense for expense in expenses}
        
        for snap in snaps:      #Gathering snapshot data

            expense = expenses_ID[snap.expense_id]

            if expense.status:      #Checks to see if expense is not deleted

                if snap.expense_id in active_expenses:     #Updates data in dict
                    expense = active_expenses[snap.expense_id]
                    expense["earning"] += snap.expense_earnings
                    expense["spending"] += snap.total_spending
                    expense["credit_balance"] += snap.credit_balance
                    
                else:       #Creates new key-val pair [name, earnings, spending]
                    active_expenses[snap.expense_id] = {"name": snap.expense_name, "earning": snap.expense_earnings, "spending": snap.total_spending, "credit_balance": snap.credit_balance}             
            
            else:

                if snap.expense_id in inactive_expenses:
                    expense = inactive_expenses[snap.expense_id]
                    expense["earning"] += snap.expense_earnings
                    expense["spending"] += snap.total_spending
                    expense["credit_balance"] += snap.credit_balance
                
                else:
                    inactive_expenses[snap.expense_id] = {"name": snap.expense_name, "earning": snap.expense_earnings, "spending": snap.total_spending, "credit_balance": snap.credit_balance}             
            

        overview_stats = {"Balance": 0.0, "Earnings": 0.0, "Transferred": 0.0, "Spendings": 0.0, "Savings": 0.0, "Credit_Balance": 0.0}      #Gather's user overview

        #Combines all the expense id's in a list to update for overview_stats
        all_expense_id = list(active_expenses.keys()) + list(inactive_expenses.keys())

        for expense_id in all_expense_id:       #Updating overview stats 
            expense = Expenses.query.filter_by(id = expense_id).first()
            
            #Picks which dictionary to use
            expense_dict = None

            if expense_id in active_expenses:
                expense_dict = active_expenses
            else:
                expense_dict = inactive_expenses
            

            #Deriving other forms of data from the spending/earning 
            earnings = expense_dict[expense_id]["earning"]
            expense_dict[expense_id]["earning"] = round(earnings, 2)

            spending = expense_dict[expense_id]["spending"]
            expense_dict[expense_id]["spending"] = round(spending, 2)

            transferred = round(float(expense.transferred), 2)
            expense_dict[expense_id]["transferred"] = transferred
            expense.transferred = transferred

            balance = round(float(transferred + earnings), 2)
            expense_dict[expense_id]["balance"] = balance
            expense.balance = balance

            saving = round(float(balance - spending), 2)
            expense_dict[expense_id]["saving"] = round(saving, 2)
            expense.savings = saving

            if balance != 0:
                saving_percent = round((saving/balance)*100, 2)
                spending_percent = round((spending/balance)*100, 2)
                
            else:
                saving_percent = 0
                spending_percent = 0
                
            expense_dict[expense_id]["spending_percent"] = spending_percent
            expense_dict[expense_id]["saving_percent"] = saving_percent


            
            #Setting overview stats
            overview_stats["Balance"] += balance
            

            overview_stats["Earnings"] += earnings
            expense.set_earnings(earnings)
            
            overview_stats["Transferred"] += transferred
            
            overview_stats["Spendings"] += spending
            expense.set_spending(spending)
            
            expense.set_savings()
            overview_stats["Savings"] += saving

            expense.credit_balance += expense_dict[expense_id]["credit_balance"]
            overview_stats["Credit_Balance"] += expense_dict[expense_id]["credit_balance"]


        for stat in overview_stats:
            overview_stats[stat] = round(overview_stats[stat], 2)

        db.session.commit()
        
        spending = Spending.query.filter_by(user_id = session["user_id"]).all()


        return render_template("summary.html", user = helper.get_user(session["user_id"]), active_expenses = active_expenses, inactive_expenses = inactive_expenses, lifetime_stats = overview_stats, spending = spending, all_expense_id = all_expense_id)
    

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
                flash("Profile update was successful!")
                return redirect(url_for("user.profile"))
            else:
                flash("Your password does not match, please try again.")
                return redirect(url_for("user.edit_profile"))
            

    else:
        return redirect(url_for("user.login"))
    



#Used for retrieving data for plots
@user.route("/spending_income_data")
def get_spending_income_data():
    if helper.check_login():
        entries = Entry.query.filter_by(user_id = session["user_id"]).all()
        spendings = Spending.query.filter_by(user_id = session["user_id"]).all()

        dates_income = [entry.date for entry in entries]
        income = [entry.income for entry in entries]

        dates_spending = []
        for spending in spendings:
            if spending.date in dates_spending:
                pass
            else:
                dates_spending.append(spending.date)
        
        spending = [spending.amount for spending in spendings]



        data = {
            "dates_income": dates_income,
            "income": income,
            "dates_spending": dates_spending,
            "spending":spending
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

        spendings = Spending.query.filter_by(user_id = session["user_id"]).all()

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




@user.route("/charts", methods = ["POST", "GET"])
def charts():
    if helper.check_login():
        if request.method == "POST":
            return render_template("charts.html")
        else:
            return redirect(url_for("user.summary"))
    else:
        return redirect(url_for("user.login"))

