from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from app.models import User, Expenses, Entry, Spending, Exp_Snap
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

                return redirect(url_for("entry.all_entry"))
            
            else:       #User expenses don't add to 100%
                flash("expenses do not add to 100")
                return redirect(url_for("entry.expenses"))
    else:
        return redirect(url_for("user.login"))


@entry.route("/display_entry/<entry_id>", methods=["POST", "GET"])
def display_entry(entry_id):
    if helper.check_login():
        snapshots = Exp_Snap.query.filter_by(entry_id = int(entry_id)).all()        #Gets all data associated w/ requested entry
        entry = Entry.query.filter_by(id = int(entry_id)).first()
        
        if request.method == "GET":
            for snapshot in snapshots:      #Calculate expense earnings using entry's total earned
                earnings = round((entry.income * snapshot.expense_percentage/100), 2)
                snapshot.set_earnings(earnings)
            
        db.session.commit()
        return render_template("display_entry.html", snapshots = snapshots, entry = entry)
    
    else:
        return redirect(url_for("user.login"))
    


@entry.route("/delete_entry/<entry_id>", methods=["POST"])
def delete_entry(entry_id):
    if helper.check_login():
        if request.method == "POST":        #Deletes all data assoicated with requested entry
            entry = Entry.query.filter_by(user_id = session["user_id"], id = int(entry_id)).first()
            snaps = Exp_Snap.query.filter_by(entry_id = entry_id).delete()
            spendings = Spending.query.filter_by(entry_id = entry_id).delete()
        
            db.session.delete(entry)
            db.session.commit()
        return redirect(url_for("entry.entry"))
    
    else:
        return redirect(url_for("user.login"))


@entry.route("/add_income/<entry_id>", methods = ["POST"])
def add_income(entry_id):
    if helper.check_login():
        if request.method == "POST":
            income = float(request.form.get("income"))
            current_entry = Entry.query.filter_by(user_id = session["user_id"], id = int(entry_id)).first()
            current_entry.add_money(income)
            return redirect(url_for("entry.display_entry", entry_id = entry_id))
        
        else:
            return redirect(url_for("entry.entry"))
        
    else:
        return redirect(url_for("user.login"))