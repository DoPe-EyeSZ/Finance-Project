from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from app.models import User, Expenses, Entry, Spending, Exp_Snap
from app import helper
import os
from app import db

spending = Blueprint("spending", __name__, template_folder="templates")

@spending.route("/add_spending/<int:snap_id>", methods = ["POST"])
def add_spending(snap_id):
    if helper.check_login():
        if request.method == "POST":
            snap = Exp_Snap.query.filter_by(id = int(snap_id)).first()      #Gets neccesary data
            amount = float(request.form.get("spending"))        
            reasoning = str(request.form.get("reasoning"))

            transaction = Spending(snap.entry_id, snap.expense_name, session["user_id"], snap.expense_id, amount, reasoning)     #Add spending to DB
            db.session.add(transaction)

            snap.add_spending(float(amount))

        db.session.commit()
        return redirect(url_for("entry.view_entry", entry_id = snap.entry_id))
    else:
        return redirect(url_for("user.login"))
