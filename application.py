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
import json
from os.path import basename as get_plot_title, splitext
import uuid
from pathlib import Path
import threading
from pandas import DataFrame
from datetime import datetime
from core.strudel_interface import validate_date, StrudelInterface
from analytics.visulisation import Visualisation
from core.APPLE import APPLE
from shutil import rmtree

path = str(Path().absolute())
home_dir_abs = str(Path().absolute().parent.parent)


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


def update_request_status(request_id: str, status_update: str, request_list: list) -> None:
    """
    Def to update status of API tasks
    :param request_id: str
            Request ID of the request to update
    :param status_update: str
            What to update the status to
    :param request_list:
            The list of requests that could be updated
    :return: Nothing
    """
    for a_task in request_list:
        if a_task["request_id"] == request_id:
            a_task["request_status"] = status_update


def add_to_request_status(request_id: str, key_to_add: str, value_to_add: str,request_list: list) -> None:
    """
    Def to update status of API tasks
    :param value_to_add: str
            Value to add to request json for key_to_add
    :param key_to_add: str
            Key to add to the request json
    :param request_id: str
            Request ID of the request to update
    :param request_list:
            The list of requests that could be updated
    :return: Nothing
    """
    for a_task in request_list:
        if a_task["request_id"] == request_id:
            a_task[key_to_add] = value_to_add


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
                         job_name = task['task_id'])
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
    rmtree(temp_dir.parent)
    update_task_status(task_id = task["task_id"], status_update = "Complete",
                       task_list = task_list)


# --- API is defined from here to end

application = Flask(__name__)
# location to make / store databse in
db_loc = 'sqlite:///users_db_apple/users.db'

if not os.path.exists("users_db_apple"):
    os.mkdir("users_db_apple")

application.config['SQLALCHEMY_DATABASE_URI'] = db_loc
application.config['SECRET_KEY'] = str(uuid.uuid4())
application.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(application)
auth = HTTPBasicAuth()

# list used to store all task dicts
tasks = []
vis_requests = []

accepting_new_users = True


# class for user administration
class User(db.Model):
    _tablename_ = "users"
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password_hash = db.Column(db.String(128))

    def hash_password(self, password: str) -> None:
        """
        Def to hash passed password
        :param password: str
                password to hash (plain text)
        :return: Nothing
        """
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Def to verify password hash
        :param password: str
                password (plain text)
        :return: bool
                True if password when hashed is equal to the passed hash
        """
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, token_validity_length: int = 600) -> json:
        """
        Def to generate auth token
        :param token_validity_length: int
                Length of time, in seconds, that generated token is valid for
        :return: json
        """
        return jwt.encode(
            {'id': self.id, 'exp': time.time() + token_validity_length},
            application.config['SECRET_KEY'], algorithm = 'HS256'
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
            data = jwt.decode(token, application.config['SECRET_KEY'],
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


@application.route('/', methods=['GET'])
def health() -> json:
    """
    EB uses this route to check health of the app, setting this up so it remains
    healthy
    """
    return jsonify({'health': "healthy"})


@application.route('/apple/api/v1.0/newuser', methods=['POST'])
def new_user() -> json:
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
        return make_response(jsonify({'user': username,
                                      "status": "created"}), 201)
    else:
        return jsonify({"Error": "Cannot register new users at this time"})


@application.route('/apple/api/v1.0/generatetoken', methods = ['GET'])
@auth.login_required
def get_auth_token():
    """
    Endpoint to generate an auth token for a user
    :return: json
    """
    token = g.user.generate_auth_token(600)
    return make_response(jsonify({'token': token.decode('ascii'), 'duration': 600}))


@application.errorhandler(404)
def not_found():
    """
    Return error message
    :return: json
    """
    return make_response(jsonify({'error': 'Not found'}), 404)


@application.errorhandler(400)
def not_found():
    """
    Return error message
    :return: json
    """
    return make_response(jsonify({'error': 'Not found'}), 400)


@application.route('/apple/api/v1.0/tasks', methods = ['GET'])
@auth.login_required
def get_tasks():
    """
    Endpoint to return all tasks
    :return: json
    """
    return make_response(jsonify({'tasks': tasks}))


@application.route('/apple/api/v1.0/tasks', methods = ['POST'])
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


@application.route('/apple/api/v1.0/tasks/<int:task_id>', methods = ['GET'])
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


# --- Visualisation endpoints

supported_vis_types = ["volatility", "time_series", "stratified_performance"]
# this will need to be ported to a request to get data from STRUDEL
# aggregated_data_filepath = "data/aggregated_results/20_21/predictions_and_results_log.csv"


@application.route('/analytics/api/v1.0/visualisations', methods = ['POST'])
@auth.login_required
def create_visualisations():
    """"
    Endpoint to create a visualisation
    :return: json
    """
    # check if type is specified
    if not request.json or 'type' not in request.json:
        abort(400)
    # check type passed
    if request.json["type"] not in supported_vis_types:
        abort(400)
    # create task id
    request_id = str(uuid.uuid4())
    vis_request = {
        "request_id": request_id,
        "type": request.json["type"],
        "request_status": "Submitted"
    }
    vis_requests.append(vis_request)
    # creat a vis object here
    if vis_request["type"] == "volatility":
        update_request_status(request_id = request_id, status_update = "Generating", request_list = vis_requests)
        visualisation_thread = threading.Thread(target = generate_and_return_visualisation, args = ("volatility", request_id,request.json,))
        visualisation_thread.start()
    elif vis_request["type"] == "time_series":
        update_request_status(request_id = request_id, status_update = "Generating", request_list = vis_requests)
        visualisation_thread = threading.Thread(target = generate_and_return_visualisation, args = ("time_series", request_id,request.json,))
        visualisation_thread.start()
    elif vis_request["type"] == "stratified_performance":
        update_request_status(request_id = request_id, status_update = "Generating", request_list = vis_requests)
        visualisation_thread = threading.Thread(target = generate_and_return_visualisation,
                                                args = ("time_series", request_id,request.json,))
        visualisation_thread.start()
    else:
        update_request_status(request_id = request_id, status_update = "Error", request_list = vis_requests)
        add_to_request_status(request_id = request_id, key_to_add = "Error message",
                              value_to_add = "Error in implementation of visualisation for visualisation type {}. Please see terminal for more information".format(vis_request["type"]),
                              request_list = vis_requests)
        return jsonify({'request': vis_request}), 201
    return jsonify({'request': vis_request}), 201


@application.route('/analytics/api/v1.0/visualisations/all', methods = ['POST'])
@auth.login_required
def create_all_visualisations():
    """"
    Endpoint to create a all visualisations
    :return: json
    """
    request_id = str(uuid.uuid4())
    vis_request = {
        "request_id": request_id,
        "type": "all",
        "request_status": "Submitted"
    }
    if "date" in request.json:
        vis_request["date"] = request.json["date"]
    vis_requests.append(vis_request)
    # create vis object
    update_request_status(request_id = request_id, status_update = "Generating", request_list = vis_requests)
    visualisation_thread = threading.Thread(target = generate_and_return_visualisation,
                                            args = ("all", request_id, vis_request,))
    visualisation_thread.start()
    return jsonify({'request': vis_request}), 201


@application.route('/analytics/api/v1.0/visualisations', methods = ['GET'])
@auth.login_required
def get_all_requests():
    """
    Return all vis requests as json
    :return:
    """
    return jsonify({'tasks': vis_requests})


@application.route('/apple/api/v1.0/temporarydata', methods = ['DELETE'])
@auth.login_required
def delete_temporary_data():
    """"
    Endpoint to create a all visualisations
    :return: json
    """
    temp_dir = path + "/temporary_data/"
    rmtree(temp_dir)
    return jsonify({'Temporary Data Dir': "deleted"}), 201


def generate_and_return_visualisation(vis_type: str, request_id: str, full_request: dict) -> None:
    """
    Def to generate visualisations and return them to STRUDEL
    :param vis_type: str
            Type of visualisations to generate
    :param request_id: str
            Request id
    :param full_request: dict
    :return: nothing
    """
    # create temp data loc
    temp_dir_str = path + "/temporary_data/" + request_id
    temp_dir = Path(temp_dir_str)
    if not temp_dir.exists():
        temp_dir.mkdir(parents = True)
    # create STRUDEL connection to get f
    # trs and predictions from start of the season up until today
    strudel_connection = StrudelInterface(credentials_filepath = path + '/credentials/credentials.json')
    # first day of the season
    start_date = "2020-09-12"
    if "date" in full_request:
        end_date = full_request["date"]
    else:
        end_date = datetime.today().strftime("%Y-%m-%d")
    historical_data_loc = "temporary_data/" + request_id + "/historical_data.csv"
    strudel_connection.get_predictions_and_ftrs(start_date= start_date,
                                                end_date = end_date,
                                                output_loc = historical_data_loc)
    visualizer = Visualisation(aggregated_data_filepath = historical_data_loc, show_visualisations = False)
    if vis_type == "all":
        plots_to_return_to_strudel = [temp_dir_str + "/weekly_winner.html",
                                      temp_dir_str + "/overall_winner.html",
                                      temp_dir_str + "/volatility.html",
                                      temp_dir_str + "/time_series.html",
                                      temp_dir_str + "/stratified_performance_top_6_teams.html",
                                      temp_dir_str + "/stratified_performance_newly_promoted_teams.html",
                                      ]
        visualizer.weekly_winner(output_filepath = plots_to_return_to_strudel[0])
        visualizer.total_winner(output_filepath = plots_to_return_to_strudel[1])
        visualizer.volatility(output_filepath = plots_to_return_to_strudel[2])
        visualizer.time_series(output_filepath = plots_to_return_to_strudel[3])
        visualizer.stratified_performance(metric = "top 6 teams",
                                          output_filepath = plots_to_return_to_strudel[4])
        visualizer.stratified_performance(metric = "newly promoted teams",
                                          output_filepath = plots_to_return_to_strudel[5])
    elif vis_type == "volatility":
        plots_to_return_to_strudel = [temp_dir_str + "/volatility.html"]
        visualizer.volatility(output_filepath = plots_to_return_to_strudel[0])
    elif vis_type == "time_series":
        plots_to_return_to_strudel = [temp_dir_str + "/time_series.html"]
        visualizer.time_series(output_filepath = temp_dir + plots_to_return_to_strudel[0])
    elif vis_type == "stratified_performance":
        mertic_formatted_for_output_str = full_request["metric"].replace(" ", "_")
        plots_to_return_to_strudel = [temp_dir_str + "/stratified_performance_" + mertic_formatted_for_output_str + ".html"]
        visualizer.stratified_performance(metric = full_request["metric"],
                                          output_filepath = plots_to_return_to_strudel[0])
    else:
        update_request_status(request_id = request_id, status_update = "Error", request_list = vis_requests)
        add_to_request_status(request_id = request_id, key_to_add = "Error Message", value_to_add = "Unexpected type of visualisation requested", request_list = vis_requests)
        raise Exception("Unexpected Type")
    update_request_status(request_id = request_id, status_update = "Uploading", request_list = vis_requests)
    # make list of failures if any
    failures = [splitext(get_plot_title(plot))[0] for plot in plots_to_return_to_strudel if not strudel_connection.return_visualisations(html_filepath = plot, visualisation_title = splitext(get_plot_title(plot))[0], notes = "dummy1, dummy2", request_id = request_id)]
    if len(failures) >= 1:
        update_request_status(request_id = request_id, status_update = "Partially Complete", request_list = vis_requests)
        add_to_request_status(request_id = request_id, key_to_add = "Plot(s) failed to load", value_to_add = ",".join(failures), request_list = vis_requests)
    else:
        # delete temporary storage
        rmtree(temp_dir)
        rmtree(temp_dir.parent)
        update_request_status(request_id = request_id, status_update = "Complete", request_list = vis_requests)


if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()
    # run app here
    application.run(debug = False)
