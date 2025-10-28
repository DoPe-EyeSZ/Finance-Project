from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from app.models import User, Expenses, Entry, Spending, Exp_Snap
import os
from app import db

main = Blueprint("main", __name__, template_folder="templates")

@main.route("/")
@main.route("/home")
def home():

    return render_template("home.html")


@main.route("/dash")
def dash():
    return render_template("dash.html")


#------------------------------------------------USER INFO--------------------------------
@main.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":    #Executes after login

        inputted_email = request.form["email"]      #Stores inputted pw and email 
        inputted_pw = request.form["pw"]       
        user = User.query.filter_by(email = inputted_email).first()      #Searches for user with inputted email
        


        if user:      #Checks if user exists
            if inputted_pw == user.pw:      #Login Successful

                session["user_id"] = user.id     #Save user ID to session
                session["name"] = user.name
                return redirect(url_for("main.dash"))
            
            else:     #Email exist but name!=pw

                flash("wrong pw or email")
                return render_template("login.html")  
            
        else:     #Email does not exist

            flash("email no exist")
            return render_template("login.html")

    else:       #User went to login page unconventionally
        if "user_id" in session:
            return redirect(url_for("main.dash"))
        else:
            return render_template("login.html")



@main.route("/logout")
def logout():
    if "user_id" in session:
        flash("You've successfully logged out", "info")
    else:
        flash("You're not even logged in lol", "info")
    
    session.clear()     #Deletes user ID and name from session
    
    return redirect(url_for("main.login"))



@main.route("/signup", methods = ["POST", "GET"])   
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
            return redirect(url_for("main.dash"))
        
    else:        #User just clicks on signup button
        return render_template("signup.html")


@main.route("/delete")
def delete():        #Deletes User account from DB
    if "user_id" in session:
        user = get_user(session["user_id"])

        user_expense = Expenses.query.filter_by(user_id = session["user_id"]).delete()

        user_entry = Entry.query.filter_by(user_id = session["user_id"]).delete()

        user_spending = Spending.query.filter_by(user_id = session["user_id"]).delete()

        user_snapshot = Exp_Snap.query.filter_by(user_id = session["user_id"]).delete()

        db.session.delete(user)
        db.session.commit()
        flash("deleted successfully")
    else:
        flash("nothing deleted")
       
    return redirect(url_for("main.logout"))



@main.route("/stats", methods=["GET"])
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

                spending_percent = round(((expense[2]/expense[1]) * 100), 2)
                saving_percent = round((((expense[1] - expense[2]) * 100 )/expense[1]), 2)

                expense[4] = spending_percent
                expense[5] = saving_percent


            else:
                if snap.expense_earnings == 0:
                    data[snap.expense_id] = [snap.expense_name, 0, 0, 0, 0]

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
        return render_template("stats.html", name = get_user(session["user_id"]).name, data = data, lifetime_stats = lifetime_stats)
    

    else:
        return render_template("login.html")
    

#--------------------------------------------EXPENSES-------------------------------
@main.route("/expenses", methods = ["POST", "GET"])
def expenses():
    if check_login():

        if request.method == "POST":        #Adds a new expense
            inputted_expense = request.form["expense_name"]
            inputted_percentage = float(request.form["percent"])
            expense = Expenses(session["user_id"], inputted_expense.upper(), inputted_percentage)
            db.session.add(expense)
            db.session.commit()
            return redirect(url_for("main.expenses"))

        else:       #Displays all expenses that are active
            valid_expenses = Expenses.query.filter_by(user_id = session["user_id"], status = True).all()
            return render_template("expenses.html", expenses = valid_expenses, status = calculate_percentage(session["user_id"]))        #only shows expenses not deleted by user
    else:
        return redirect(url_for("main.login")) 
        

@main.route("/edit_expense/<expense_id>", methods = ["POST"])     
def edit_expense(expense_id):
    if check_login():

        if request.method == "POST":        #Edits an expense
            new_name = request.form.get("name")
            new_percent = request.form.get("percentage")
            old_expense = Expenses.query.filter_by(id = expense_id).first()
            old_expense.change_name(new_name.upper())
            old_expense.change_percentage(new_percent)

        db.session.commit()
        return redirect(url_for("main.expenses"))
    
    else:
        return redirect(url_for("main.login")) 



@main.route("/delete_expense/<expense_id>", methods = ["POST"])
def delete_expense(expense_id):
    if check_login():
        if request.method == "POST":        
            snap = Exp_Snap.query.filter_by(expense_id = expense_id).all()
            removed_expense = Expenses.query.filter_by(id = expense_id).first()

            if len(snap)>0:     #Takes expense from display if it is in use
                removed_expense.status = False
                
            else:       #Permanently deletes expense if not in use
                db.session.delete(removed_expense)


            db.session.commit()
            return redirect(url_for("main.expenses"))
        
    else:
        return redirect(url_for("main.login"))


def calculate_percentage(user_id):
    expenses = Expenses.query.filter_by(user_id = user_id, status = True).all()
    total = 0
    for expense in expenses:
        if expense.status == True:      #Checks if the expense was deleted by user
            total += expense.percentage
    
    if total!=100:
        return [total, False]
    else:
        return [total, True]


#----------------------------------------------Entries


@main.route("/entry", methods = ["GET"])
def entry():
    if check_login():

        if request.method == "GET":     #Displays all user entries
            return render_template("entry.html", entries = Entry.query.filter_by(user_id = session["user_id"]).all())
    else:
        return redirect(url_for("main.login"))
        

@main.route("/add_entry", methods = ["POST"])
def add_entry():
    if check_login():

        if request.method == "POST":
            if calculate_percentage(session["user_id"])[1]:     #Only creates new entry if current expenses add to 100%  
                new_entry = Entry(session["user_id"])   
                db.session.add(new_entry)
                expenses = Expenses.query.filter_by(user_id = session["user_id"], status = True).all()      #Retrieve current expenses

                for expense in expenses:        #Saves all current expense data 
                    snapshot = Exp_Snap(new_entry.id, session["user_id"], expense.id, expense.name, expense.percentage)
                    db.session.add(snapshot)

                db.session.commit()     #Saves all changes/additions

                return redirect(url_for("main.entry"))
            
            else:       #User expenses don't add to 100%
                flash("expenses do not add to 100")
                return redirect(url_for("main.expenses"))
    else:
        return redirect(url_for("main.login"))


@main.route("/display_entry/<entry_id>", methods=["POST", "GET"])
def display_entry(entry_id):
    if check_login():
        snapshots = Exp_Snap.query.filter_by(entry_id = int(entry_id)).all()        #Gets all data associated w/ requested entry
        entry = Entry.query.filter_by(id = int(entry_id)).first()
        
        if request.method == "GET":
            for snapshot in snapshots:      #Calculate expense earnings using entry's total earned
                earnings = round((entry.income * snapshot.expense_percentage/100), 2)
                snapshot.set_earnings(earnings)
            
        db.session.commit()
        return render_template("display_entry.html", snapshots = snapshots, entry = entry)
    
    else:
        return redirect(url_for("main.login"))
    


@main.route("/delete_entry/<entry_id>", methods=["POST"])
def delete_entry(entry_id):
    if check_login():
        if request.method == "POST":        #Deletes all data assoicated with requested entry
            entry = Entry.query.filter_by(user_id = session["user_id"], id = int(entry_id)).first()
            snaps = Exp_Snap.query.filter_by(entry_id = entry_id).delete()
            spendings = Spending.query.filter_by(entry_id = entry_id).delete()
        
            db.session.delete(entry)
            db.session.commit()
        return redirect(url_for("main.entry"))
    
    else:
        return redirect(url_for("main.login"))


@main.route("/add_income/<entry_id>", methods = ["POST"])
def add_income(entry_id):
    if check_login():
        if request.method == "POST":
            income = float(request.form.get("income"))
            current_entry = Entry.query.filter_by(user_id = session["user_id"], id = int(entry_id)).first()
            current_entry.add_money(income)
            return redirect(url_for("main.display_entry", entry_id = entry_id))
        
        else:
            return redirect(url_for("main.entry"))
        
    else:
        return redirect(url_for("main.login"))
    





#-------------------------------------------------------SPENDING-------------------------------

@main.route("/add_spending/<int:snap_id>", methods = ["POST"])
def add_spending(snap_id):
    if check_login():
        if request.method == "POST":
            snap = Exp_Snap.query.filter_by(id = int(snap_id)).first()      #Gets neccesary data
            amount = float(request.form.get("spending"))        
            reasoning = str(request.form.get("reasoning"))

            transaction = Spending(snap.entry_id, session["user_id"], snap.expense_id, amount, reasoning)     #Add spending to DB
            db.session.add(transaction)

            snap.add_spending(float(amount))

        db.session.commit()
        return redirect(url_for("main.display_entry", entry_id = snap.entry_id))
    else:
        return redirect(url_for("main.login"))



#-------------------HELPER METHODS--------------------
@main.route("/admin")        #Admin page
def admin():
    if "user_id" in session:
        user = get_user(session["user_id"])
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


def get_user(identification):        #Method to get user by id
    return User.query.filter_by(id = identification).first()

def get_expenses(identification):
    return Expenses.query.filter_by(user_id = identification).all()

def check_login():
    return "user_id" in session