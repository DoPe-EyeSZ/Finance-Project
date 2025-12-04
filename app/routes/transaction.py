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

            transaction = Transaction( snap.expense_name, session["user_id"], snap.expense_id, amount, snap.entry_id,reasoning)     #Add spending to DB
            db.session.add(transaction)
            snap.add_spending(float(amount))

        db.session.commit()
        return redirect(url_for("entry.view_entry", entry_id = snap.entry_id))
    else:
        return redirect(url_for("user.login"))


@transaction.route("/edit_transaction_amount/<transaction_id>", methods = ["POST"])
def edit_transaction_amount(transaction_id):
    if helper.check_login():
        
        
        if request.method == "POST":
            transaction = Transaction.query.filter_by(id = transaction_id).first()
            new_amount = float(request.form.get("amount"))

            #Changing deposit amount
            if transaction.deposit_status:
                transaction.amount = new_amount
                db.session.commit()

                if transaction.entry_id is not None:        #For deposit from entries 
                    return redirect(url_for("entry.view_entry", entry_id = transaction.entry_id))
                
                else:       #For deposits from manage expenses
                    return redirect(url_for("expense.expenses"))
                
            #Changing spending amount    
            else:       
                #Needed to edit amount spent for expense
                snap = Exp_Snap.query.filter_by(entry_id = transaction.entry_id, expense_id = transaction.expense_id).first()
                reimburse = new_amount - transaction.amount
                snap.add_spending(reimburse)
                transaction.amount = new_amount
                db.session.commit()
                return redirect(url_for("entry.view_entry", entry_id = transaction.entry_id))
            

    else:
        return redirect(url_for("user.login"))    


@transaction.route("/delete_transaction/<transaction_id>", methods = ["POST"])
def delete_transaction(transaction_id):
    if helper.check_login():
        #Grabs data associated with desired spending (spending column, snapshot of expense)
        transaction = Transaction.query.filter_by(id = transaction_id).first()
        source = request.form.get("source")

        #Deleting deposits
        if transaction.deposit_status:
            db.session.delete(transaction)

            if source == "entry":        #Goes to entry deposit from entries 
                db.session.commit()
                return redirect(url_for("entry.view_entry", entry_id = transaction.entry_id))
            
            else:       #For deposits from manage expenses
                db.session.commit()
                return redirect(url_for("expense.expenses"))
            
        else:
            #Editing spending/credit balance numbers
            snap = Exp_Snap.query.filter_by(entry_id = transaction.entry_id, expense_id = transaction.expense_id).first()
            transaction_amount = transaction.amount

            if transaction.credit_status:       #Subtracts total credit spending
                snap.credit_balance -= transaction_amount
            
            else:        #Subtracts total debit spending
                snap.total_spending-=transaction_amount

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