from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from app.models import User, Expenses, Entry, Transaction, Exp_Snap
from app import helper
import os
from app import db

transaction = Blueprint("transaction", __name__, template_folder="templates")

@transaction.route("/add_spending/<int:snap_id>", methods = ["POST"])
def add_spending(snap_id):
    if helper.check_login():

        snap = Exp_Snap.query.filter_by(id = int(snap_id)).first()      #Gets neccesary data
        amount = float(request.form.get("spending"))        
        reasoning = str(request.form.get("reasoning"))
        if request.method == "POST":

            #    def __init__(self, expense_name, user_id, expense_id, amount, entry_id=None, reasoning=None):

            transaction = Transaction( snap.expense_name, session["user_id"], snap.expense_id, amount, snap.entry_id,reasoning)     #Add spending to DB
            db.session.add(transaction)
            snap.add_spending(float(amount))

        db.session.commit()
        return redirect(url_for("entry.view_entry", entry_id = snap.entry_id))
    else:
        return redirect(url_for("user.login"))


@transaction.route("/edit_spending/<spending_id>", methods = ["POST"])
def edit_spending(spending_id):
    if helper.check_login():
        spending = Transaction.query.filter_by(id = spending_id).first()
        snap = Exp_Snap.query.filter_by(entry_id = spending.entry_id, expense_id = spending.expense_id).first()
        if request.method == "POST":
            new_amount = float(request.form.get("amount"))
            reimburse = new_amount - spending.amount

            snap.add_spending(reimburse)
            spending.amount = request.form.get("amount")
            db.session.commit()
        
        return redirect(url_for("entry.view_entry", entry_id = spending.entry_id))

    else:
        return redirect(url_for("user.login"))    


@transaction.route("/delete_spending/<spending_id>", methods = ["POST"])
def delete_spending(spending_id):
    if helper.check_login():
        #Grabs data associated with desired spending (spending column, snapshot of expense)
        transaction = Transaction.query.filter_by(id = spending_id).first()
        snap = Exp_Snap.query.filter_by(entry_id = transaction.entry_id, expense_id = transaction.expense_id).first()

        if request.method == "POST":
            transaction_amount = transaction.amount

            if transaction.credit_status:       #Subtracts total credit spending
                snap.credit_balance -= transaction_amount
            
            elif not transaction.deposit_status:        #Subtracts total debit spending
                snap.add_spending(-transaction_amount)

            db.session.delete(transaction)
            db.session.commit()

        return redirect(url_for("entry.view_entry", entry_id = transaction.entry_id))
    else:
        return redirect(url_for("user.login"))
    

@transaction.route("/add_credit/<int:snap_id>", methods = ["POST"])
def add_credit(snap_id):
    if helper.check_login():

        snap = Exp_Snap.query.filter_by(id = int(snap_id)).first()      #Gets neccesary data
        amount = float(request.form.get("spending"))        
        reasoning = str(request.form.get("reasoning"))
        if request.method == "POST":

            transaction = Transaction(snap.expense_name, session["user_id"], snap.expense_id, amount, snap.entry_id, reasoning)     #Add spending to DB
            transaction.credit_status = True
            snap.add_credit(amount)
            db.session.add(transaction)

        db.session.commit()
        return redirect(url_for("entry.view_entry", entry_id = snap.entry_id))
    else:
        return redirect(url_for("user.login"))


@transaction.route("/pay_credit/<spending_id>", methods = ["POST"])
def pay_credit(spending_id):
    if helper.check_login():
        credit_spending = Transaction.query.filter_by(id = int(spending_id)).first()
        snap = Exp_Snap.query.filter_by(entry_id = credit_spending.entry_id, expense_id = credit_spending.expense_id).first()

        if request.method == "POST":
            amount = float(credit_spending.amount)
            credit_spending.credit_status = False
            snap.add_spending(amount)
            snap.credit_balance -= amount
            
        db.session.commit()
        return redirect(url_for("entry.view_entry", entry_id = snap.entry_id))
    else:
        return redirect(url_for("user.login"))
    

@transaction.route("/update_transaction_date/<spending_id>", methods = ["POST"])
def update_transaction_date(spending_id):
    if helper.check_login():
        spending = Transaction.query.filter_by(id = int(spending_id)).first()
        if request.method == "POST":
            new_date = request.form.get("new_date")
            spending.date = new_date
            db.session.commit()
            return redirect(url_for("entry.view_entry", entry_id = int(spending.entry_id)))
    
    else:
        return redirect(url_for("user.login"))
    

@transaction.route("/edit_reasoning/<spent_id>", methods = ["POST"])
def edit_reasoning(spent_id):
    if helper.check_login():
        spending = Transaction.query.filter_by(id = int(spent_id)).first()
        if request.method == "POST":
            new = request.form.get("reasoning")
            spending.reasoning = new
            db.session.commit()
            return redirect(url_for("entry.view_entry", entry_id = int(spending.entry_id)))

    else:
        return redirect(url_for("user.login"))