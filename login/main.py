from functools import wraps

from flask import Flask, make_response
from flask import render_template, request, session, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, exists
import smtplib
from datetime import timedelta
import re

MYMAIL = 'experimentdawn56@gmail.com'
KEY = 'kmcm pkdj hgpu qezw'
SECRET = "SEC"


class Base(DeclarativeBase):
    pass


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///information.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
app.secret_key = SECRET
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class Store(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    key: Mapped[str] = mapped_column(String(8), nullable=False)
    mail: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


def is_strong_password(password):
    pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return re.match(pattern, password)


@app.before_request
def session_timeout():
    session.permanent = True
    session.modified = True


@app.route('/')
def home():
    return render_template('open.html')


@app.route('/<name>/')
def red(name):
    if name == 'login':
        return render_template('login.html')
    if name == 'signin':
        return render_template('signin.html')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('red', name='login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login/send', methods=["GET", "POST"])
def check():
    if request.method == "POST":
        username = request.form.get("uname")
        password = request.form.get("psw")
        with app.app_context():
            query = db.session.query(exists().where(Store.name == username))
        if query.scalar():
            with app.app_context():
                fish = db.session.execute(db.select(Store).where(Store.name == username)).scalar()
            if fish.key == password:
                session['user'] = username
                session['mail'] = fish.mail
                flash("Welcome!!! back sir")
                return redirect(url_for('dash'))

            else:
                flash("Wrong Password, Re-enter your credentials")
                return redirect(url_for('red', name='login'))
        else:
            error_msg = "You dont exist, please sign in "
            flash(error_msg)
            return redirect(url_for('red', name='signin'))


@app.route('/signin/send', methods=["GET", "POST"])
def give():
    if request.method == "POST":
        username = request.form.get("uname")
        password1 = request.form.get("psw1")
        password2 = request.form.get("psw2")
        email = request.form.get("email")

        if password1 != password2:
            error_msg = "The passwords don't match. Try again."
            flash(error_msg)
            return redirect(url_for('red', name='signin'))

        if not is_strong_password(password1):
            error_msg = "Password not strong enough"
            flash(error_msg)
            return redirect(url_for('red', name='signin'))

        with app.app_context():
            existing_user = db.session.query(Store).filter_by(mail=email).first()
            if existing_user:
                error_msg = "This user is already registered. Please log in."
                flash(error_msg)
                return redirect(url_for('red', name='login'))

            new_user = Store(name=username, key=password1, mail=email)
            db.session.add(new_user)
            db.session.commit()

        session['user'] = username
        session['mail'] = email
        flash("Welcome, new user!")
        return redirect(url_for('dash'))


@app.route('/forgot-password')
def forgot():
    return render_template('forgotpass.html')


@app.route('/forgot-password/transfer', methods=["POST"])
def email():
    if request.method == "POST":
        email = request.form.get("email")

        with app.app_context():
            user = db.session.query(Store).filter_by(mail=email).first()

        if user:
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(MYMAIL, KEY)
                message = f"Subject: Password Recovery\n\nYour password is: {user.key}"
                server.sendmail(MYMAIL, email, message)
                server.quit()

                msg = "The password has been sent to your email. Check the spam, if not found."
                flash(msg)
                return redirect(url_for('red', name='login'))
            except Exception as e:
                error_msg = "Failed to send email. Please try again later."
                flash(error_msg)
                return redirect(url_for('forgot'))
        else:
            error_msg = "You are a new user. Please Sign in."
            flash(error_msg)
            return redirect(url_for('red', name='signin'))


@app.route('/dashboard')
@login_required
def dash():
    u = session['user']
    m = session['mail']
    response = make_response(render_template('dashboard.html', u=u, m=m))

    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response

# @app.route('/upload', methods=['POST'])
# def pictures():
#     u = session['user']
#     if request.method == 'POST':
#         tit = request.form.get("filename")
#         des = request.form.get("desc")
#         pict = request.files['pic']
#         mime = pict.mimetype
#         project = Img(img=pict.read(), mimetype=mime, title=tit, description=des, owner=u)
#         imgdb.session.add(project)
#         imgdb.session.commit()
#     return redirect(url_for('dash'))
#
#


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.clear()
    error_msg = "You have been logged out"
    flash(error_msg)
    return redirect(url_for('home'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
