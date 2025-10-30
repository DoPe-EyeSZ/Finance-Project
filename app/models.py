from app import db
from datetime import date

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

    def change_percentage(self, new_percent):
        self.percentage = new_percent

    def set_earnings(self, amount):
        self.earnings = amount

    def add_earnings(self, amount):
        self.earnings +=amount

    def set_spending(self, amount):
        self.spendings = amount

    def set_savings(self):
        self.savings = self.earnings - self.spendings
    
    



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
    
    def set_earnings(self, amount):
        self.expense_earnings = amount

    def get_savings(self):
        savings = round((self.expense_earnings - self.total_spending), 2)
        return savings