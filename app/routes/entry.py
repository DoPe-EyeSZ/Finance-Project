from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from app.models import User, Expenses, Entry, Transaction, Exp_Snap
from app import helper
from .expense import calculate_percentage
import os
from app import db

entry = Blueprint("entry", __name__, template_folder="templates")


@entry.route("/entry", methods = ["GET"])
def all_entry():
    if helper.check_login():

        if request.method == "GET":     #Displays all user entries
            return render_template("entry.html", entries = Entry.query.filter_by(user_id = session["user_id"]).all())
    else:
        return redirect(url_for("user.login"))
        

@entry.route("/add_entry", methods = ["POST"])
def add_entry():
    if helper.check_login():

        if request.method == "POST":
            if calculate_percentage(session["user_id"])[1]:     #Only creates new entry if current expenses add to 100%  
                new_entry = Entry(session["user_id"])   
                db.session.add(new_entry)
                expenses = Expenses.query.filter_by(user_id = session["user_id"], status = True).all()      #Retrieve current expenses

                for expense in expenses:        #Saves all current expense data 
                    snapshot = Exp_Snap(new_entry.id, session["user_id"], expense.id, expense.name, expense.percentage)
                    db.session.add(snapshot)

                db.session.commit()     #Saves all changes/additions

                return redirect(url_for("entry.view_entry", entry_id = new_entry.id))
            
            else:       #User expenses don't add to 100%
                flash("Your expense allocation must total 100%. Please review and adjust your values.", "error")
                return redirect(url_for("expense.expenses"))
    else:
        return redirect(url_for("user.login"))


@entry.route("/entry/view_entry/<entry_id>", methods=["GET"])
def view_entry(entry_id):
    if helper.check_login():
        snapshots = Exp_Snap.query.filter_by(entry_id = int(entry_id)).all()        #Gets all data associated w/ requested entry
        entry = Entry.query.filter_by(id = int(entry_id)).first()
        
        est_balance = {}        #Links the expense's total savings (amount able to spend) to the snapshot of the expense
        if request.method == "GET":
            

            for snapshot in snapshots:      #Calculate expense earnings using entry's total earned
                earnings = round((entry.income * snapshot.expense_percentage/100), 2)
                snapshot.set_earnings(earnings)
                savings = helper.calc_savings(snapshot.expense_id)      #Calculates the total savings to send to front

                est_balance[snapshot] = round(savings,2)

            spending = Transaction.query.filter_by(entry_id = entry_id).all()
            total_spent = 0
            for spend in spending:
                if not spend.credit_status:
                    total_spent += spend.amount

            total_spent = round(total_spent, 2)
            net_earnings = round(entry.income - total_spent, 2)

            db.session.commit()
            return render_template("view_entry.html", snapshots = snapshots, entry = entry, est_balance = est_balance, spending = spending, net_earnings = net_earnings, total_spent = total_spent)
        else:
            return redirect(url_for("entry.all_entry"))
    
    else:
        return redirect(url_for("user.login"))
    


@entry.route("/delete_entry/<entry_id>", methods=["POST"])
def delete_entry(entry_id):
    if helper.check_login():
        if request.method == "POST":        #Deletes all data assoicated with requested entry
            entry = Entry.query.filter_by(id = int(entry_id)).first()
            spendings = Transaction.query.filter_by(entry_id = entry_id).delete()
            snaps = Exp_Snap.query.filter_by(entry_id = entry_id).delete()
            db.session.delete(entry)
            db.session.commit()


            #If a deleted expense does not hold user data then permanently delete expense
            expenses = Expenses.query.filter_by(user_id = session["user_id"], status = False).all()
            for expense in expenses:
                remaining_snaps = Exp_Snap.query.filter_by(expense_id = expense.id).count()
                if remaining_snaps ==0:
                    db.session.delete(expense)
                    db.session.commit()
            
        
            
        return redirect(url_for("entry.all_entry"))
    
    else:
        return redirect(url_for("user.login"))


@entry.route("/add_income/<entry_id>", methods = ["POST"])
def add_income(entry_id):
    if helper.check_login():
        if request.method == "POST":
            income = float(request.form.get("income"))
            current_entry = Entry.query.filter_by(user_id = session["user_id"], id = int(entry_id)).first()
            current_entry.add_money(income)
            db.session.commit()
            return redirect(url_for("entry.view_entry", entry_id = entry_id))
        
        else:
            return redirect(url_for("entry.all_entry"))
        
    else:
        return redirect(url_for("user.login"))
    

@entry.route("/update_date/<entry_id>", methods = ["POST"])
def update_date(entry_id):
    if helper.check_login():
        entry = Entry.query.filter_by(id = int(entry_id)).first()
        if request.method == "POST":
            new_date = request.form.get("new_date")
            entry.date = new_date
            db.session.commit()
            return redirect(url_for("entry.view_entry", entry_id = entry_id))
    else:
        return redirect(url_for("user.login"))
    

@entry.route("/entry_deposit", methods = ["POST"])
def transfer():
    
    if helper.check_login():
        snap_id = request.form.get("snap_id")
        amount = request.form.get("amount")
        snap = Exp_Snap.query.filter_by(id = int(snap_id)).first()

        expense = Expenses.query.filter_by(id = int(snap.expense_id)).first()        #FIGUREOUT WHY NOT COMMITING CHANGES

        expense.transfer_in(float(amount))

        db.session.commit()
        return redirect(url_for("entry.view_entry", entry_id = snap.entry_id))

    else:
        return redirect(url_for("user.login"))