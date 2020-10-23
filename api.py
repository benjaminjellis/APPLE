from flask import Flask, jsonify, make_response, request, abort
import uuid
from pathlib import Path
import threading

from core.strudel_interface import validate_date
from core.APPLE import APPLE


path = str(Path().absolute())


def update_task_status(task_id: str, status_update: str, task_list: list) -> None:
    for a_task in task_list:
        if a_task["task_id"] == task_id:
            a_task["task_status"] = status_update


def rest_apple_interface(task: dict, task_list: list) -> None:
    """
    Def used to run APPLE in a new thread
    :param task:
    :param task_list:
    :return: nothing
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
    apple_predictions_filepath = apple_object.run(return_filepath = True)
    # use STRUDEL endpoint here to return the above results
    if task['cleanup'] == "true":
        update_task_status(task_id = task["task_id"], status_update = "Cleaning up saved models directories",
                           task_list = task_list)
        apple_object.cleanup()
    temp_dir.rmdir()
    update_task_status(task_id = task["task_id"], status_update = "Complete",
                       task_list = task_list)


app = Flask(__name__)
tasks = []


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/apple/api/v1.0/tasks', methods = ['GET'])
def get_tasks():
    return jsonify({'tasks': tasks})


@app.route('/apple/api/v1.0/tasks', methods = ['POST'])
def create_task():
    """"
    POST - used to create an APPLE object and perform a prediction run
    :return:
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
def get_task(task_id):
    task = [task for task in tasks if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
        return jsonify({'task': task[0]})


if __name__ == '__main__':
    app.run(debug = True)