import json

from argon2.exceptions import VerifyMismatchError
from flask import Flask, g, jsonify, render_template, redirect, url_for, flash
from flask_login import (current_user, LoginManager, login_required,
                         login_user, logout_user)

from auth import auth
import config
import forms
import models
from resources.todos import todos_api
from resources.users import users_api

app = Flask(__name__)
app.register_blueprint(todos_api, url_prefix='/api/v1')
app.register_blueprint(users_api, url_prefix='/api/v1')
app.secret_key = config.SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'signup'


@app.route('/')
def my_todos():
    return render_template('index.html')


@login_manager.user_loader
def load_user(id):
    return models.User.get_or_none(id=id)


@app.before_request
def before_request():
    g.user = current_user


@app.route('/signup', methods=('GET', 'POST'))
def signup():
    form = forms.SignupForm()
    if form.validate_on_submit():
        models.User.create_user(
            username=form.username.data,
            password=form.password.data
        )
        user = models.User.get(models.User.username == form.username.data)
        login_user(user)
        return redirect(url_for('my_todos'))
    return render_template('signup.html', form=form)


@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.username == form.username.data)
        except models.User.DoesNotExist:
            flash('Sign in failed.')
        else:
            try:
                user.verify_password(form.password.data)
            except VerifyMismatchError:
                flash('Sign in failed.')
            else:
                login_user(user)
                return redirect(url_for('my_todos'))
    return render_template('login.html', form=form)


@app.route('/logout', methods=('GET', 'POST'))
@login_required
def logout():
    logout_user()
    return redirect(url_for('my_todos'))


@app.route('/api/v1/users/token', methods=['GET'])
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


if __name__ == '__main__':
    models.initialize()

    if models.Todo.select().count() == 0:
        data = json.load(open('mock/todos.json'))
        for todo in data:
            models.Todo.create(name=todo.get('name'), completed=False)

    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
