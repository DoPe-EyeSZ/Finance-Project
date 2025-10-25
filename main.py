from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from dotenv import load_dotenv
import os
from datetime import timedelta


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///budget.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_PERMANENT"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)



db = SQLAlchemy(app)


class User(db.Model):        #Stores all user info
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(25))
    name = db.Column(db.String(25))
    pw = db.Column(db.String(25))


    def __init__(self, email, pw, name):
        self.email = email
        self.name = name
        self.pw = pw


class Expenses(db.Model):        #Stores all expense category per user
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String(25))
    percentage = db.Column(db.Float)
    status = db.Column(db.Boolean, default = True)
    savings = db.Column(db.Float, default = 0.0) 
    earnings = db.Column(db.Float, default = 0.0)
    spendings = db.Column(db.Float, default = 0.0)

    def __init__(self, user_id, name, percentage):
        self.user_id = user_id
        self.name = name
        self.percentage = percentage

    def change_name(self, new_name):
        self.name = new_name
        db.session.commit()

    def change_percentage(self, new_percent):
        self.percentage = new_percent
        db.session.commit()

    def set_earnings(self, amount):
        self.earnings = amount
        db.session.commit()

    def set_spending(self, amount):
        self.spendings = amount
        db.session.commit()

    def set_savings(self):
        self.savings = self.earnings - self.spendings
        db.session.commit()
    



class Entry(db.Model):        #Stores each entry per user
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    income = db.Column(db.Float, default = 0.0)
    date = db.Column(db.Integer, default = date.today())

    def __init__(self, user_id):
        self.user_id = user_id

    
    def add_money(self, money):
        self.income += float(money)
        self.income = round(self.income, 2)
        db.session.commit()


class Spending(db.Model):        #Stores every spending per entry
    id = db.Column(db.Integer, primary_key = True)
    entry_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    expense_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    reasoning = db.Column(db.String(100), default = "")

    def __init__(self, entry_id, user_id, expense_id, amount, reasoning=None):
        if reasoning:
            self.entry_id = entry_id
            self.user_id = user_id
            self.expense_id = expense_id
            self.reasoning = reasoning
            self.amount = amount
        else:
            self.entry_id = entry_id
            self.user_id = user_id
            self.expense_id = expense_id
            self.amount = amount


class Exp_Snap(db.Model):       #Stores a snapshot of the expense
    id = db.Column(db.Integer, primary_key = True)
    entry_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    expense_id = db.Column(db.Integer)
    expense_name = db.Column(db.String)
    expense_percentage = db.Column(db.Float)
    expense_earnings = db.Column(db.Float, default = 0.0)
    total_spending = db.Column(db.Float, default = 0.0)
    
    def __init__(self, entry_id, user_id, expense_id, expense_name, expense_percentage):
        self.user_id = user_id
        self.entry_id = entry_id
        self.expense_id = expense_id
        self.expense_name = expense_name
        self.expense_percentage = expense_percentage

    def add_spending(self, amount):
        self.total_spending += amount
        self.total_spending = round(self.total_spending, 2)
        db.session.commit()
    
    def set_earnings(self, amount):
        self.expense_earnings = amount
        db.session.commit()

    def get_savings(self):
        savings = round((self.expense_earnings - self.total_spending), 2)
        return savings

     



@app.route("/")
@app.route("/home")
def home():

    return render_template("home.html")


#------------------------------------------------USER INFO--------------------------------
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":    #Executes after login

        inputted_email = request.form["email"]      #Stores inputted pw and email 
        inputted_pw = request.form["pw"]       
        user = User.query.filter_by(email = inputted_email).first()      #Searches for user with inputted email
        


        if user:      #Checks if user exists
            if inputted_pw == user.pw:      #Login Successful

                session["user_id"] = user.id     #Save user ID to session
                session["name"] = user.name
                return redirect(url_for("stats"))
            
            else:     #Email exist but name!=pw

                flash("wrong pw or email")
                return render_template("login.html")  
            
        else:     #Email does not exist

            flash("email no exist")
            return render_template("login.html")

    else:       #User went to login page unconventionally
        if "user_id" in session:
            return redirect(url_for("stats"))
        else:
            return render_template("login.html")



@app.route("/logout")
def logout():
    if "user_id" in session:
        flash("You've successfully logged out", "info")
    else:
        flash("You're not even logged in lol", "info")
    
    session.clear()     #Deletes user ID and name from session
    
    return redirect(url_for("login"))



@app.route("/signup", methods = ["POST", "GET"])   
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
            return redirect(url_for("stats"))
        
    else:        #User just clicks on signup button
        return render_template("signup.html")


@app.route("/delete")
def delete():        #Deletes User account from DB
    if "user_id" in session:
        user = get_user(session["user_id"])

        user_expense = Expenses.query.filter_by(user_id = session["user_id"]).all()
        for expense in user_expense:
            db.session.delete(expense)
            db.session.commit()

        user_entry = Entry.query.filter_by(user_id = session["user_id"]).all()
        for entry in user_entry:
            db.session.delete(entry)
            db.session.commit()

        user_spending = Spending.query.filter_by(user_id = session["user_id"]).all()
        for spending in user_spending:
            db.session.delete(spending)
            db.session.commit()

        user_snapshot = Exp_Snap.query.filter_by(user_id = session["user_id"]).all()
        for snap in user_snapshot:
            db.session.delete(snap)
            db.session.commit()

        db.session.delete(user)
        db.session.commit()
        flash("deleted successfully")
    else:
        flash("nothing deleted")
    return redirect(url_for("logout"))



@app.route("/stats", methods=["GET"])
def stats():
    if "user_id" in session:
        data = {}
        snaps = Exp_Snap.query.filter_by(user_id = session["user_id"]).all()
        
        for snap in snaps:
            if snap.expense_id in data:                #key is the expense id; value is arr[name, earning, spending]
                expense = data[snap.expense_id]
                expense[1] += snap.expense_earnings
                expense[2] += snap.total_spending

                spending_percent = round((expense[2]/expense[1]), 2) * 100
                saving_percent = round(((expense[1] - expense[2])/expense[1]), 2) * 100

                expense[4] = spending_percent
                expense[5] = saving_percent


            else:       #Adds to data dict
                if snap.expense_earnings == 0:
                    data[snap.expense_id] = [snap.expense_name, 0, 0, 0, 0]
                else:
                    spending_percent = round((snap.total_spending/snap.expense_earnings), 2) * 100
                    saving_percent = round(((snap.expense_earnings - snap.total_spending)/snap.expense_earnings), 2) * 100
                    data[snap.expense_id] = [snap.expense_name, snap.expense_earnings, snap.total_spending, snap.get_savings(), spending_percent, saving_percent]
        
        for info in data:       #Updating stats for each expense
            expense = Expenses.query.filter_by(id = info).first()
            expense.set_earnings(data[info][1])
            expense.set_spending(data[info][2])
            expense.set_savings()
            db.session.commit()
        
        return render_template("stats.html", name = get_user(session["user_id"]).name, data = data)
    

    else:
        return render_template("login.html")
    

#--------------------------------------------EXPENSES-------------------------------
@app.route("/expenses", methods = ["POST", "GET"])
def expenses():
    if check_login():

        if request.method == "POST":        #Adds a new expense
            inputted_expense = request.form["expense_name"]
            inputted_percentage = float(request.form["percent"])
            expense = Expenses(session["user_id"], inputted_expense.upper(), inputted_percentage)
            db.session.add(expense)
            db.session.commit()
            return redirect(url_for("expenses"))

        else:       #Displays all expenses that are active
            valid_expenses = Expenses.query.filter_by(user_id = session["user_id"], status = True).all()
            return render_template("expenses.html", expenses = valid_expenses, status = calculate_percentage(session["user_id"]))        #only shows expenses not deleted by user
    else:
        return redirect(url_for("login")) 
        

@app.route("/edit_expense/<expense_id>", methods = ["POST"])     
def edit_expense(expense_id):
    if check_login():

        if request.method == "POST":        #Edits an expense
            new_name = request.form.get("name")
            new_percent = request.form.get("percentage")
            old_expense = Expenses.query.filter_by(id = expense_id).first()
            old_expense.change_name(new_name.upper())
            old_expense.change_percentage(new_percent)

        return redirect(url_for("expenses"))
    
    else:
        return redirect(url_for("login")) 



@app.route("/delete_expense/<expense_id>", methods = ["POST"])
def delete_expense(expense_id):
    if check_login():

        if request.method == "POST":        
            snap = Exp_Snap.query.filter_by(expense_id = expense_id).all()
            removed_expense = Expenses.query.filter_by(id = expense_id).first()

            if len(snap)>0:     #Takes expense from display if it is in use
                removed_expense.status = False
                db.session.commit()
                
            else:       #Permanently deletes expense if not in use
                db.session.delete(removed_expense)
                db.session.commit()

            return redirect(url_for("expenses"))
        
    else:
        return redirect(url_for("login"))


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


@app.route("/entry", methods = ["GET"])
def entry():
    if check_login():

        if request.method == "GET":     #Displays all user entries
            return render_template("entry.html", entries = Entry.query.filter_by(user_id = session["user_id"]).all())
    else:
        return redirect(url_for("login"))
        

@app.route("/add_entry", methods = ["POST"])
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

                return redirect(url_for("entry"))
            
            else:       #User expenses don't add to 100%
                flash("expenses do not add to 100")
                return redirect(url_for("expenses"))
    else:
        return redirect(url_for("login"))


@app.route("/display_entry/<entry_id>", methods=["POST", "GET"])
def display_entry(entry_id):
    if check_login():
        snapshots = Exp_Snap.query.filter_by(entry_id = int(entry_id)).all()        #Gets all data associated w/ requested entry
        entry = Entry.query.filter_by(id = int(entry_id)).first()
        
        if request.method == "GET":
            for snapshot in snapshots:      #Calculate expense earnings using entry's total earned
                earnings = round((entry.income * snapshot.expense_percentage/100), 2)
                snapshot.set_earnings(earnings)
        return render_template("display_entry.html", snapshots = snapshots, entry = entry)
    
    else:
        return redirect(url_for("login"))
    


@app.route("/delete_entry/<entry_id>", methods=["POST"])
def delete_entry(entry_id):
    if check_login():
        if request.method == "POST":        #Deletes all data assoicated with requested entry
            entry = Entry.query.filter_by(user_id = session["user_id"], id = int(entry_id)).first()
            snaps = Exp_Snap.query.filter_by(entry_id = entry_id).all()
            spendings = Spending.query.filter_by(entry_id = entry_id).all()

            for snap in snaps:
                db.session.delete(snap)
                db.session.commit()
            
            for spending in spendings:
                db.session.delete(spending)
                db.session.commit()
        
            db.session.delete(entry)
            db.session.commit()
        return redirect(url_for("entry"))
    
    else:
        return redirect(url_for("login"))


@app.route("/add_income/<entry_id>", methods = ["POST"])
def add_income(entry_id):
    if check_login():
        if request.method == "POST":
            income = float(request.form.get("income"))
            current_entry = Entry.query.filter_by(user_id = session["user_id"], id = int(entry_id)).first()
            current_entry.add_money(income)
            return redirect(url_for("display_entry", entry_id = entry_id))
        
        else:
            return redirect(url_for("entry"))
        
    else:
        return redirect(url_for("login"))
    





#-------------------------------------------------------SPENDING-------------------------------

@app.route("/add_spending/<int:snap_id>", methods = ["POST"])
def add_spending(snap_id):
    if check_login():
        if request.method == "POST":
            snap = Exp_Snap.query.filter_by(id = int(snap_id)).first()      #Gets neccesary data
            amount = float(request.form.get("spending"))        
            reasoning = str(request.form.get("reasoning"))

            transaction = Spending(snap.entry_id, session["user_id"], snap.expense_id, amount, reasoning)     #Add spending to DB
            db.session.add(transaction)
            db.session.commit()

            snap.add_spending(float(amount))

        return redirect(url_for("display_entry", entry_id = snap.entry_id))
    else:
        return redirect(url_for("login"))



#-------------------HELPER METHODS--------------------
@app.route("/view")        #View all users in the DB
def view():

    info = []
    for user in User.query.all():
        user_expense = Expenses.query.filter_by(user_id = user.id).all()
        user_entry = Entry.query.filter_by(user_id = user.id).all()
        user_snapshots = Exp_Snap.query.filter_by(user_id = user.id).all()
        user_spending = Spending.query.filter_by(user_id = user.id).all()

        info.append({"User": user, "Expenses": user_expense, "Entry": user_entry, "Snapshot": user_snapshots, "Spending": user_spending})

    return render_template("view.html", info = info)


def get_user(identification):        #Method to get user by id
    return User.query.filter_by(id = identification).first()

def get_expenses(identification):
    return Expenses.query.filter_by(user_id = identification).all()

def check_login():
    if "user_id" in session:
        return True
    else:
        return False






if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)