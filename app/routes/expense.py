from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from app.models import User, Expenses, Entry, Spending, Exp_Snap
from app import helper
import os
from app import db

expense = Blueprint("expense", __name__, template_folder="templates")


@expense.route("/expenses", methods = ["GET"])
def expenses():
    if helper.check_login():
        active_expenses = Expenses.query.filter_by(user_id = session["user_id"], status = True).all()
        inactive_expenses = Expenses.query.filter_by(user_id = session["user_id"], status = False).all()
        return render_template("expenses.html", active_expenses = active_expenses, inactive_expenses = inactive_expenses, status = calculate_percentage(session["user_id"]))        #Shows all expenses
    
    else:
        return redirect(url_for("user.login")) 
        

@expense.route("/add_expense", methods = ["POST"])
def add_expense():
    if helper.check_login():

        if request.method == "POST":        #Adds a new expense
            inputted_expense = request.form["expense_name"]
            inputted_percentage = float(request.form["percent"])
            expense = Expenses(session["user_id"], inputted_expense.upper(), inputted_percentage)
            db.session.add(expense)
            db.session.commit()

        return redirect(url_for("expense.expenses"))
    
    else:
        return redirect(url_for("user.login"))

@expense.route("/edit_expense/<expense_id>", methods = ["POST"])     
def edit_expense(expense_id):
    if helper.check_login():

        if request.method == "POST":        #Edits an expense
            new_name = request.form.get("name")
            new_percent = request.form.get("percentage")
            old_expense = Expenses.query.filter_by(id = expense_id).first()
            old_expense.change_name(new_name.upper())
            old_expense.change_percentage(new_percent)

        db.session.commit()
        return redirect(url_for("expense.expenses"))
    
    else:
        return redirect(url_for("user.login")) 



@expense.route("/archive_expense/<expense_id>", methods = ["POST"])
def archive_expense(expense_id):
    if helper.check_login():
        if request.method == "POST":        
            snap_count = Exp_Snap.query.filter_by(expense_id = expense_id).count()
            removed_expense = Expenses.query.filter_by(id = expense_id).first()

            #If expense still holds user data, then don't display; Otherwise permanently delete expense
            if snap_count>0:    
                removed_expense.status = False
                
            else:       
                db.session.delete(removed_expense)
                flash("there does not seem to be data for this expense")


            db.session.commit()
            return redirect(url_for("expense.expenses"))
        
    else:
        return redirect(url_for("user.login"))
    

@expense.route("/deposit", methods = ["POST"])
def deposit():
    
    if helper.check_login():
        expense_id = request.form.get("expense_id")
        amount = request.form.get("amount")

        expense = Expenses.query.filter_by(id = int(expense_id)).first()        #FIGUREOUT WHY NOT COMMITING CHANGES

        expense.add_deposit(float(amount))

        db.session.commit()
        return redirect(url_for("user.stats"))

    else:
        return redirect(url_for("user.login"))


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