from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from app.models import User, Expenses, Entry, Transaction, Exp_Snap
import os
from app import db

helper = Blueprint("help", __name__, template_folder="templates")



def get_user(identification):        #Method to get user by id
    return User.query.filter_by(id = identification).first()

def get_expenses(identification):
    return Expenses.query.filter_by(user_id = identification).all()

def check_login():
    return "user_id" in session

def calc_savings(expense_id):
    #Grabs distributed income and spending data
    snaps = Exp_Snap.query.filter_by(expense_id = expense_id).all()     

    #Grabs deposit data
    deposits = Transaction.query.filter_by(expense_id = expense_id, user_id = session["user_id"], deposit_status = True).all()

    earnings = 0
    for deposit in deposits:        #Calculating total deposit for desired expense
        earnings += deposit.amount
        
    spending = 0
    for snap in snaps:      #Calculating total spending and income for desired expense
        earnings += snap.expense_earnings
        spending += snap.total_spending

    
    return round(earnings-spending, 2)      #Returns savings amount