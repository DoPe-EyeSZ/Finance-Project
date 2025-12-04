from .entry import entry
from .expense import expense
from .transaction import transaction
from .user import user

def register_blueprint(app):
    app.register_blueprint(entry)
    app.register_blueprint(expense)
    app.register_blueprint(transaction)
    app.register_blueprint(user)