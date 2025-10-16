from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date


app = Flask(__name__)
app.secret_key = "zp7kkOFK4C308RoC2wXWw7pz2"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///budget.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



db = SQLAlchemy(app)


class User(db.Model):        #Stores all user info
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(25))
    pw = db.Column(db.String(25))
    name = db.Column(db.String(25))


    def __init__(self, email, pw, name):
        self.email = email
        self.pw = pw
        self.name = name


class Expenses(db.Model):        #Stores all expense category per user
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String(25))
    percentage = db.Column(db.Float)

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


class Entry(db.Model):        #Stores each entry per user
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    income = db.Column(db.Float)
    date = db.Column(db.Integer)            #FIGURE OUT HOW TO ADD DATE LATER

    def __init__(self, user_id):
        self.user_id = user_id
        self.income = 0
        self.date = date.today()
    
    def add_money(self, money):
        self.income += float(money)
        db.session.commit()


class Spending(db.Model):        #Stores every spending per entry
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer)
    entry_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    reasoning = db.Column(db.String(100))

    def __init__(self, entry_id, amount, reasoning):
        self.entry_id = entry_id
        self.amount = amount
        self.reasoning = reasoning


class Saving(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer)
    savings = db.Column(db.Float)

     



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

                session["id"] = user.id     #Save user ID to session
                flash("login worked")
                return redirect(url_for("stats"))
            
            else:     #Email exist but name!=pw

                flash("wrong pw or email")
                return render_template("login.html")  
            
        else:     #Email does not exist

            flash("email no exist")
            return render_template("login.html")

    else:       #User went to login page unconventionally
        if "id" in session:
            return redirect(url_for("stats"))

    return render_template("login.html")



@app.route("/logout")
def logout():
    if "id" in session:
        flash("You've successfully logged out", "info")
    else:
        flash("You're not even logged in lol", "info")
    
    session.pop("id", None)     #Deletes user ID and name from session
    session.pop("name", None)
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
            session["id"] = usr.id
            return redirect(url_for("stats"))
        
    else:        #User just clicks on signup button
        return render_template("signup.html")


@app.route("/delete")
def delete():        #Deletes User account from DB
    if "id" in session:
        user = get_user(session["id"])
        user_expense = Expenses.query.filter_by(user_id = session["id"]).all()
        for expense in user_expense:
            db.session.delete(expense)
            db.session.commit()

        user_entry = Entry.query.filter_by(user_id = session["id"]).all()
        for entry in user_entry:
            db.session.delete(entry)
            db.session.commit()

        user_spending = Spending.query.filter_by(user_id = session["id"]).all()
        for spending in user_spending:
            db.session.delete(spending)
            db.session.commit()

        db.session.delete(user)
        db.session.commit()
        flash("deleted successfully")
    else:
        flash("nothing deleted")
    return redirect(url_for("logout"))



@app.route("/stats", methods=["POST", "GET"])
def stats():
    return render_template("stats.html", name = get_user(session["id"]).name)
    

#--------------------------------------------EXPENSES-------------------------------
@app.route("/expenses", methods = ["POST", "GET"])
def expenses():                          
    if request.method == "POST":
        inputted_expense = request.form["expense_name"]
        inputted_percentage = float(request.form["percent"])

        expense = Expenses(session["id"], inputted_expense, inputted_percentage)
        db.session.add(expense)
        db.session.commit()

        return redirect(url_for("expenses"))

    else:
        if "id" in session:
            return render_template("expenses.html", expenses = Expenses.query.filter_by(user_id = session["id"]).all(), status = calculate_percentage(session["id"]))
        else:
            return redirect(url_for("login")) 
        

@app.route("/edit_expense/<expense_id>", methods = ["POST", "GET"])     
def edit_expense(expense_id):
    if request.method == "POST":
        new_name = request.form.get("name")
        new_percent = request.form.get("percentage")

        old_expense = Expenses.query.filter_by(id = expense_id).first()

        old_expense.change_name(new_name)
        old_expense.change_percentage(new_percent)

    return redirect(url_for("expenses"))


@app.route("/delete_expense/<expense_id>", methods = ["POST", "GET"])
def delete_expense(expense_id):
    if request.method == "POST":
        removed_expense = Expenses.query.filter_by(id = expense_id).first()
        db.session.delete(removed_expense)
        db.session.commit()

    return redirect(url_for("expenses"))


def calculate_percentage(user_id):
    expenses = Expenses.query.filter_by(user_id = user_id).all()
    total = 0
    for expense in expenses:
        total += expense.percentage
    
    if total!=100:
        return [total, "Does not equate to 100%", False]
    else:
        return [total, "Perfect", True]


#----------------------------------------------Entries


@app.route("/entry", methods = ["POST", "GET"])
def entry():
    if request.method == "POST":

        return redirect(url_for("entry"))

    else:
        if "id" in session:
            return render_template("entry.html", entries = Entry.query.filter_by(user_id = session["id"]).all())
        else:
            return redirect(url_for("login"))
        

@app.route("/add_entry", methods = ["POST", "GET"])
def add_entry():
    if request.method == "POST":
        user_id = session["id"]
        entry = Entry(user_id)
        db.session.add(entry)
        db.session.commit()
    return redirect(url_for("entry"))


@app.route("/display_entry/<entry_id>", methods=["POST", "GET"])
def display_entry(entry_id):
    print("reached")
    expenses = Expenses.query.filter_by(user_id = session["id"]).all()
    print(f"ID: {entry_id}")
    entry = Entry.query.filter_by(id = int(entry_id)).first()                   #FIX THIS   FIX THIS   FIX THIS   FIX THIS   FIX THIS   FIX THIS   FIX THIS   FIX THIS   FIX THIS   FIX THIS   FIX THIS   

    if "id" in session:
        return render_template("display_entry.html", expenses = expenses, entry = entry)
    else:
        return redirect(url_for("login"))
        


@app.route("/delete_entry/<entry_id>", methods=["POST", "GET"])
def delete_entry(entry_id):
    if request.method == "POST":
        entry = Entry.query.filter_by(user_id = session["id"], id = int(entry_id)).first()
        db.session.delete(entry)
        db.session.commit()
        return redirect(url_for("entry"))
    else:
        if "id" in session:
            return redirect(url_for("entry"))
        else:
            return redirect(url_for("login"))


@app.route("/add_income/<entry_id>", methods = ["POST"])
def add_income(entry_id):
    if "id" in session:
        if request.method == "POST":
            if calculate_percentage(session["id"])[2]:
                income = float(request.form.get("income"))
                current_entry = Entry.query.filter_by(user_id = session["id"], id = int(entry_id)).first()
                current_entry.add_money(income)
            else:
                flash("Allocation to Expenses do not add to 100")
        return redirect(url_for("display_entry", entry_id = entry_id))
    else:
        return redirect(url_for("logout"))
    
'''
@app.route("/delete_entries")
def delete_entries():
    if "id" in session:
        entries = Entry.query.filter_by(user_id = session["id"]).all()
        for entry in entries:
            db.session.delete(entry)
            db.session.commit()
        return redirect(url_for("view"))
'''




#-------------------------------------------------------SPENDING-------------------------------


#-------------------HELPER METHODS--------------------
@app.route("/view")        #View all users in the DB
def view():

    info = []
    for user in User.query.all():
        user_expense = Expenses.query.filter_by(user_id = user.id).all()
        user_entry = Entry.query.filter_by(user_id = user.id).all()
        info.append({"User": user, "Expenses": user_expense, "Entry": user_entry})

    return render_template("view.html", info = info)


def get_user(identification):        #Method to get user by id
    return User.query.filter_by(id = identification).first()

def get_expenses(identification):
    return Expenses.query.filter_by(user_id = identification).all()







if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)