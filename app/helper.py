from flask import Blueprint, redirect, url_for, render_template, request, session, flash
from app.models import User, Expenses, Entry, Spending, Exp_Snap
import os
from app import db

helper = Blueprint("help", __name__, template_folder="templates")



def get_user(identification):        #Method to get user by id
    return User.query.filter_by(id = identification).first()

def get_expenses(identification):
    return Expenses.query.filter_by(user_id = identification).all()

def check_login():
    return "user_id" in session