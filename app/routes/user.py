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

                flash("wrong pw or email")
                return render_template("login.html")  
            
        else:     #Email does not exist

            flash("email no exist")
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
        flash("You're not even logged in lol", "info")
    
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
            flash("email already exists, use another one")
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
        flash("deleted successfully")
    else:
        flash("nothing deleted")
       
    return redirect(url_for("user.logout"))



@user.route("/stats", methods=["GET"])
def stats():
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

            spending = expense_dict[expense_id]["spending"]

            transferred = float(expense.transferred)
            expense_dict[expense_id]["transferred"] = transferred
            expense.transferred = transferred

            balance = float(transferred + earnings)
            expense_dict[expense_id]["balance"] = balance
            expense.balance = balance

            saving = float(balance - spending)
            expense_dict[expense_id]["saving"] = saving
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



        db.session.commit()
        spending = Spending.query.filter_by(user_id = session["user_id"]).all()



        return render_template("stats.html", user = helper.get_user(session["user_id"]), active_expenses = active_expenses, inactive_expenses = inactive_expenses, lifetime_stats = overview_stats, spending = spending, all_expense_id = all_expense_id)
    

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
                flash("update successfull")
                return redirect(url_for("user.profile"))
            else:
                flash("password does not match")
                return redirect(url_for("user.edit_profile"))
            

    else:
        return redirect(url_for("user.login"))
    


@user.route("/chart_data")
def chart_data():
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
    
@user.route("/charts")
def charts():
    return render_template("charts.html")

