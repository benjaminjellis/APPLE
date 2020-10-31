"""
REST API to run APPLE
"""

from flask import Flask, jsonify, make_response, request, abort, g, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import time
import os
import uuid
from pathlib import Path
import threading
from pandas import DataFrame
from core.strudel_interface import validate_date, StrudelInterface
from core.APPLE import APPLE
from shutil import rmtree

path = str(Path().absolute())
home_dir_abs = str(Path().absolute().parent.parent)

# Various defs


def return_apple_result_to_strudel(apple_results: DataFrame) -> None:
    """
    Def to return APPLE produced predictions to STRUDEL
    :param apple_results: DataFrame
            APPLE output DataFrame
    :return: Nothing
    """
    # crete connection to strudel
    strudel_connection = StrudelInterface(credentials_filepath = path + '/credentials/credentials.json')
    # get list of FixtureIDs
    fixture_ids = apple_results["FixtureID"].to_list()
    for fixture in fixture_ids:
        filtered_predictions = apple_results.loc[apple_results["FixtureID"] == fixture]
        fixture_predictions = {
            "prediction": filtered_predictions["APPLE Prediction"].tolist()[0],
            "homeWinProbability": filtered_predictions["p(H)"].tolist()[0],
            "drawProbability": filtered_predictions["p(D)"].tolist()[0],
            "awayWinProbability": filtered_predictions["p(A)"].tolist()[0],
            "fixture": {
                "id": fixture
            },
            "user": {
                "id": 10
            }
        }
        strudel_connection.return_predictions(prediction_details = fixture_predictions)


def update_task_status(task_id: str, status_update: str, task_list: list) -> None:
    """
    Def to update status of API tasks
    :param task_id: str
            Task ID of the task to update
    :param status_update: str
            What to update the status to
    :param task_list: list
            The list of tasks that could be updated
    :return: Nothing
    """
    for a_task in task_list:
        if a_task["task_id"] == task_id:
            a_task["task_status"] = status_update


def rest_apple_interface(task: dict, task_list: list) -> None:
    """
    Def used to run APPLE
    :param task: dict
            Dict that contains task details
    :param task_list: list
            List of all task dicts
    :return: Nothing
    """
    # create temp dir to store file used when making predictions
    temp_dir = path + "/temporary_data/" + task['task_id']
    temp_dir = Path(temp_dir)
    if not temp_dir.exists():
        temp_dir.mkdir(parents = True)
    apple_object = APPLE(use_strudel = True,
                         start_date = task['start_date'],
                         end_date = task['end_date'],
                         fixtures_to_predict = "temporary_data/" + task['task_id'] + "/" + task[
                             'task_id'] + "_fixtures_to_predict.csv",
                         # interface with STRUDEL is required here
                         data_for_predictions = task['data_for_predictions'],
                         job_name = task['job_name'],
                         week = 5)
    # check if backtesting is requested, if so complete
    if task["backtest"] == "true":
        update_task_status(task_id = task["task_id"], status_update = "Backtesting saved models", task_list = task_list)
        if "ftr" in task:
            apple_object.backtest(data_to_backtest_on = task["data_to_backtest_on"], ftrs = task["ftr"])
        else:
            apple_object.backtest(data_to_backtest_on = task["data_to_backtest_on"])
    update_task_status(task_id = task["task_id"], status_update = "Making predictions", task_list = task_list)
    apple_predictions = apple_object.run(return_results = True)
    return_apple_result_to_strudel(apple_predictions)
    # use STRUDEL endpoint here to return the above results
    if task['cleanup'] == "true":
        update_task_status(task_id = task["task_id"], status_update = "Cleaning up saved models directories",
                           task_list = task_list)
        apple_object.cleanup()
    rmtree(temp_dir)
    update_task_status(task_id = task["task_id"], status_update = "Complete",
                       task_list = task_list)


# --- API is defined from here to end

app = Flask(__name__)
# location to make / store databse in
db_loc = 'sqlite:///' + home_dir_abs + "/users_db_apple/users.db"
app.config['SQLALCHEMY_DATABASE_URI'] = db_loc
app.config['SECRET_KEY'] = str(uuid.uuid4())
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

# list used to store all task dicts
tasks = []

accepting_new_users = False


class User(db.Model):
    _tablename_ = "users"
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password_hash = db.Column(db.String(128))

    def hash_password(self, password: str) -> None:
        """
        Def to hash passed password
        :param password: str
                password (plain text)
        :return: Nothing
        """
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password: str) -> None:
        """
        Def to verify password hash
        :param password: str
                password (plain text)
        :return: Nothing
        """
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, token_validity_length: int = 600):
        """
        Def to generate auth token
        :param token_validity_length:
        :return: json
        """
        return jwt.encode(
            {'id': self.id, 'exp': time.time() + token_validity_length},
            app.config['SECRET_KEY'], algorithm = 'HS256'
        )

    @staticmethod
    def verify_auth_token(token: str):
        """
        Def to verify auth token
        :param token: str
                auth token to verify
        :return: nothing
        """
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'],
                              algorithms = ['HS256'])
        except:
            return
        return User.query.get(data['id'])

    def __repr__(self):
        return "<User %r>" % self.username


@auth.verify_password
def verify_password(username_or_token: str, password: str) -> bool:
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/apple/api/v1.0/newuser', methods=['POST'])
def new_user():
    """
    Endpoint to create new user
    :return: json
    """
    if accepting_new_users:
        username = request.json.get('username')
        password = request.json.get('password')
        if username is None or password is None:
            abort(400)    # missing arguments
        if User.query.filter_by(username=username).first() is not None:
            abort(400)    # existing user
        user = User(username=username)
        user.hash_password(password)
        db.session.add(user)
        db.session.commit()
        return (jsonify({'username': user.username}), 201,
                {'Location': url_for('get_user', id=user.id, _external=True)})
    else:
        return jsonify({"Error": "Cannot register new users at this time"})


@app.route('/apple/api/v1.0/generatetoken', methods = ['GET'])
@auth.login_required
def get_auth_token():
    """
    Endpoint to generate an auth token for a user
    :return: json
    """
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


@app.errorhandler(404)
def not_found():
    """
    Return error message
    :return: json
    """
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/apple/api/v1.0/tasks', methods = ['GET'])
@auth.login_required
def get_tasks():
    """
    Endpoint to return all tasks
    :return: json
    """
    return jsonify({'tasks': tasks})


@app.route('/apple/api/v1.0/tasks', methods = ['POST'])
@auth.login_required
def create_task():
    """"
    Endpoint to set off APPLE prediction run
    :return: json
    """
    if not request.json or 'job_name' not in request.json:
        abort(400)
    # create task id
    task_id = str(uuid.uuid4())
    task = {
        "task_id": task_id,
        'job_name': request.json['job_name'],
        'start_date': request.json['start_date'],
        'end_date': request.json['end_date'],
        'week': request.json['week'],
        'data_for_predictions': request.json['data_for_predictions'],
        'task_status': "Submitted",
        "backtest": request.json['backtest'],
        "cleanup": request.json['cleanup']
    }
    tasks.append(task)
    # validate date formats
    validate_date(date = task["start_date"])
    validate_date(date = task["end_date"])
    update_task_status(task_id = task_id, status_update = "Running", task_list = tasks)
    # set up a thread for APPLE to run in background
    apple_thread = threading.Thread(target = rest_apple_interface, args = (task, tasks,))
    apple_thread.start()
    return jsonify({'task': task}), 201


@app.route('/apple/api/v1.0/tasks/<int:task_id>', methods = ['GET'])
@auth.login_required
def get_task(task_id: str):
    """
    Endpoint to return details of specified task
    :param task_id: str
            Task ID of the task details to return
    :return: JSON
    """
    task = [task for task in tasks if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
        return jsonify({'task': task[0]})
    return jsonify({'task': task[0]})


if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()
    # run app here
    app.run(debug = False)
