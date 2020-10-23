tasks = []

task = {"status": "running", "id": "1"}
task2 = {"status": "running", "id": "2"}
tasks.append(task)
tasks.append(task2)
print(tasks)


def update_task_status(task_id: str, status_update: str, task_list: list) -> None:
    for a_task in task_list:
        if a_task["task_id"] == task_id:
            a_task["task_status"] = status_update

