from .entry import entry
from .expense import expense
from .spending import spending
from .user import user

def register_blueprint(app):
    app.register_blueprint(entry)
    app.register_blueprint(expense)
    app.register_blueprint(spending)
    app.register_blueprint(user)