from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from app.models import User, Expenses, Entry, Spending, Exp_Snap
from app import helper
import os
from app import db

user = Blueprint("user", __name__, template_folder="templates")


@user.route("/")
@user.route("/home")
def home():

    return render_template("home.html")


@user.route("/dash")
def dash():
    return render_template("dash.html")


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
            return redirect(url_for("main.dash"))
    
    else:
        return redirect(url_for("main.login"))


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
                return redirect(url_for("user.dash"))
            
            else:     #Email exist but name!=pw

                flash("wrong pw or email")
                return render_template("login.html")  
            
        else:     #Email does not exist

            flash("email no exist")
            return render_template("login.html")

    else:       #User went to login page unconventionally
        if "user_id" in session:
            return redirect(url_for("user.dash"))
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
            session["user_id"] = usr.id

            db.session.commit()
            return redirect(url_for("user.dash"))
        
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
        data = {}
        snaps = Exp_Snap.query.filter_by(user_id = session["user_id"]).all()
        
        for snap in snaps:
            if snap.expense_id in data:     #Updates data in dict
                expense = data[snap.expense_id]
                expense[1] += snap.expense_earnings
                expense[2] += snap.total_spending
                expense[3] += snap.get_savings()

                if expense[1] == 0:
                    spending_percent = 0
                    saving_percent = 0
                else:
                    spending_percent = round(((expense[2]/expense[1]) * 100), 2)
                    saving_percent = round((((expense[1] - expense[2]) * 100 )/expense[1]), 2)

                expense[4] = spending_percent
                expense[5] = saving_percent


            else:
                if snap.expense_earnings == 0:
                    data[snap.expense_id] = [snap.expense_name, 0, 0, 0, 0, 0]

                else:       #Creates new key-value pair 
                    spending_percent = round((snap.total_spending/snap.expense_earnings), 2) * 100
                    saving_percent = round(((snap.expense_earnings - snap.total_spending)/snap.expense_earnings), 2) * 100
                    data[snap.expense_id] = [snap.expense_name, snap.expense_earnings, snap.total_spending, snap.get_savings(), spending_percent, saving_percent]                #key==expense id; value==arr[name, earning, spending, saving%, spending%]
        
        lifetime_stats = {"Earnings": 0, "Spendings": 0, "Savings": 0}

        for info in data:       #Updating stats for each expense
            expense = Expenses.query.filter_by(id = info).first()

            expense.set_earnings(data[info][1])
            lifetime_stats["Earnings"] += data[info][1]

            expense.set_spending(data[info][2])
            lifetime_stats["Spendings"] += data[info][2]
            
            expense.set_savings()
            lifetime_stats["Savings"] += data[info][3]

        db.session.commit()
        return render_template("stats.html", name = helper.get_user(session["user_id"]).name, data = data, lifetime_stats = lifetime_stats)
    

    else:
        return render_template("login.html")