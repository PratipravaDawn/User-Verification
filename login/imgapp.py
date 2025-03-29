from flask_sqlalchemy import SQLAlchemy


imgdb = SQLAlchemy()


def init_img(app):
    imgdb.init_app(app)
    with app.app_context():
        imgdb.create_all()
