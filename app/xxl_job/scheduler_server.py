import importlib
from app.config.xxl_job_config import get_executor
from importlib.resources import files
from app.common.logger import log

"""
loading tasks
"""
def load_tasks():
    # unified task directory
    package_uri = "app.xxl_job.tasks"

    try:
        tasks_dir = files(package_uri)
    except Exception as e:
        raise FileNotFoundError(
            f"The package corresponding to the task directory does not exist or is inaccessible: {package_uri}") from e

        # find all matching py files
    py_files = [entry for entry in tasks_dir.iterdir()
                if entry.is_file() and entry.name.endswith(".py") and entry.name != "__init__.py"]

    if not py_files:
        raise FileNotFoundError(f"task package'{tasks_dir}' there are no available task files below")

    for entry in py_files:
        module_name = entry.name[:-3]
        full_module_name = f"{package_uri}.{module_name}"
        log.info(f"Loading task: {full_module_name}")
        importlib.import_module(full_module_name)


if __name__ == "__main__":
    load_tasks()
    # get actuator
    executor = get_executor()
    executor.run_executor()
