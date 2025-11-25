from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from app.models import User, Expenses, Entry, Spending, Exp_Snap
from app import helper
import os
from app import db

spending = Blueprint("spending", __name__, template_folder="templates")

@spending.route("/add_spending/<int:snap_id>", methods = ["POST"])
def add_spending(snap_id):
    if helper.check_login():

        snap = Exp_Snap.query.filter_by(id = int(snap_id)).first()      #Gets neccesary data
        amount = float(request.form.get("spending"))        
        reasoning = str(request.form.get("reasoning"))
        if request.method == "POST":

            transaction = Spending(snap.entry_id, snap.expense_name, session["user_id"], snap.expense_id, amount, reasoning)     #Add spending to DB
            db.session.add(transaction)
            snap.add_spending(float(amount))

        db.session.commit()
        return redirect(url_for("entry.view_entry", entry_id = snap.entry_id))
    else:
        return redirect(url_for("user.login"))


@spending.route("/edit_spending/<spending_id>", methods = ["POST"])
def edit_spending(spending_id):
    if helper.check_login():
        spending = Spending.query.filter_by(id = spending_id).first()
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


@spending.route("/delete_spending/<spending_id>", methods = ["POST"])
def delete_spending(spending_id):
    if helper.check_login():
        spending = Spending.query.filter_by(id = spending_id).first()
        snap = Exp_Snap.query.filter_by(entry_id = spending.entry_id, expense_id = spending.expense_id).first()
        entry_id = spending.entry_id

        if request.method == "POST":
            if not spending.credit_status:
                amount_added = -(spending.amount)
                snap.add_spending(amount_added)

            db.session.delete(spending)
            db.session.commit()

        return redirect(url_for("entry.view_entry", entry_id = entry_id))
    else:
        return redirect(url_for("user.login"))
    

@spending.route("/add_credit/<int:snap_id>", methods = ["POST"])
def add_credit(snap_id):
    if helper.check_login():

        snap = Exp_Snap.query.filter_by(id = int(snap_id)).first()      #Gets neccesary data
        amount = float(request.form.get("spending"))        
        reasoning = str(request.form.get("reasoning"))
        if request.method == "POST":

            transaction = Spending(snap.entry_id, snap.expense_name, session["user_id"], snap.expense_id, amount, reasoning)     #Add spending to DB
            transaction.credit_status = True
            snap.add_credit(amount)
            db.session.add(transaction)

        db.session.commit()
        return redirect(url_for("entry.view_entry", entry_id = snap.entry_id))
    else:
        return redirect(url_for("user.login"))


@spending.route("/pay_credit/<spending_id>", methods = ["POST"])
def pay_credit(spending_id):
    if helper.check_login():
        credit_spending = Spending.query.filter_by(id = int(spending_id)).first()
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
    

@spending.route("/update_transaction_date/<spending_id>", methods = ["POST"])
def update_transaction_date(spending_id):
    if helper.check_login():
        spending = Spending.query.filter_by(id = int(spending_id)).first()
        if request.method == "POST":
            new_date = request.form.get("new_date")
            spending.date = new_date
            db.session.commit()
            return redirect(url_for("entry.view_entry", entry_id = int(spending.entry_id)))
    
    else:
        return redirect(url_for("user.login"))
    

@spending.route("/edit_reasoning/<spent_id>", methods = ["POST"])
def edit_reasoning(spent_id):
    if helper.check_login():
        spending = Spending.query.filter_by(id = int(spent_id)).first()
        if request.method == "POST":
            new = request.form.get("reasoning")
            spending.reasoning = new
            db.session.commit()
            return redirect(url_for("entry.view_entry", entry_id = int(spending.entry_id)))

    else:
        return redirect(url_for("user.login"))