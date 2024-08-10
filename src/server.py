import os
import time
from datetime import datetime, timedelta
import json
import math
import shutil
from flask import Flask, Response
from flask_cors import CORS
from flask import request, send_from_directory
#
from apscheduler.schedulers.background import BackgroundScheduler
import signal

# Flask App setup____________________________________________________
static_dir = "../public"
app = Flask(__name__, static_folder=static_dir)
cors = CORS(app, origins="*")

# env
PORT = int(os.getenv(key='BACKEND_PORT', default=8888))
DATA_PATH = os.getenv(key='DATA_PATH', default="../data")
ROOT_MEDIA_PATH = os.getenv(key='ROOT_MEDIA_PATH', default="/Users/sauravahmed/Documents")
MOVIES_PATH = os.getenv(key='MEDIA_PATH', default="/Users/sauravahmed/Documents")
TV_SHOWS_PATH = os.getenv(key='TV_SHOWS_PATH', default="/Users/sauravahmed/Documents")
INTERVAL_MINUTE = int(os.getenv(key='INTERVAL_MINUTE', default=1))
CRON_HOUR = int(os.getenv(key='CRON_HOUR', default=10))
DURATION_DAYS = int(os.getenv(key='DURATION_DAYS', default=30))
DRY_RUN = os.getenv(key='DRY_RUN', default=True)


# requests___________________________________________________________

# @app.route('/info', methods=["POST"])
# def info():
#     data = request.get_json()
#     start_book_id = data.get("start_book_id", None)
#     res = {}
#     response = Response(response=res, status=200, mimetype="application/json")
#     return response


@app.route('/status', methods=["GET"])
def status():
    print("status")
    return {
        "status": "running"
    }


@app.route('/get_size_movies', methods=["GET"])
def get_movies_size():
    size = get_directory_size(MOVIES_PATH)
    human_readable_size = convert_size(size)
    return {
        "size": human_readable_size
    }


@app.route('/get_size_tvshows', methods=["GET"])
def get_tvshows_size():
    size = get_directory_size(TV_SHOWS_PATH)
    human_readable_size = convert_size(size)
    return {
        "size": human_readable_size
    }


@app.route('/get_whole_size', methods=["GET"])
def get_whole_size_():
    print("status")
    size = get_whole_size(ROOT_MEDIA_PATH)
    human_readable_size = convert_size(size.get("free"))
    return {
        "size": human_readable_size
    }


# static pages____________________________________________________
@app.route('/home')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/home/<path:path>')
def send(path):
    return send_from_directory(app.static_folder, path)


# store data____________________________________________________
def put_data(data):
    filename = f"{DATA_PATH}/files.json"
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Data successfully written to {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")


# background job____________________________________________________
def list_directories(path):
    try:
        # List all entries in the given path
        entries = os.listdir(path)
        # Filter out entries that are directories and get their full paths
        directories = [os.path.join(path, entry) for entry in entries if os.path.isdir(os.path.join(path, entry))]
        return directories
    except FileNotFoundError:
        return f"Path '{path}' does not exist."
    except PermissionError:
        return f"Permission denied for path '{path}'."


def start_scan():
    scan_dir(MOVIES_PATH)
    scan_dir(TV_SHOWS_PATH)


def get_last_modification_time(path):
    # Get the last modification time
    mod_time = os.path.getmtime(path)
    # Convert it to a readable format
    # readable_time = time.ctime(mod_time)
    # return readable_time
    return mod_time


def scan_dir(dir_path):
    directories = list_directories(dir_path)
    if isinstance(directories, list):
        print(f"Directories in '{dir_path}':")
        dir_data = []
        for directory in directories:
            last_mod = get_last_modification_time(directory)
            size = get_directory_size(directory)
            human_readable_size = convert_size(size)
            readable_time = time.ctime(last_mod)

            dir_data.append({
                'dir': directory,
                'readable_update_time': readable_time,
                'update_time': last_mod,
                'size': size,
                'human_readable_size': human_readable_size
            })
            print(f"{directory}: update: {get_last_modification_time(directory)}")

        print("# Three month old dir:")
        deu_dir_data = []
        for directory in directories:
            last_mod = get_last_modification_time(directory)
            if is_older_than_duration_days(last_mod):
                size = get_directory_size(directory)
                human_readable_size = convert_size(size)
                readable_time = time.ctime(last_mod)

                # delete task
                delete_directory(directory)
                deu_dir_data.append({
                    'dir': directory,
                    'readable_update_time': readable_time,
                    'update_time': last_mod,
                    'size': size,
                    'human_readable_size': human_readable_size
                })
                print(f"{directory}: update: {readable_time} : size: {human_readable_size}")

        put_data({'all_dir': dir_data, 'deu_dir': deu_dir_data})
    else:
        print(directories)


def is_older_than_duration_days(timestamp):
    # Convert the timestamp to a datetime object
    file_time = datetime.fromtimestamp(timestamp)
    # Get the current time
    current_time = datetime.now()
    # Calculate the time three months ago
    three_months_ago = current_time - timedelta(days=DURATION_DAYS)  # Approximate 3 months as 90 days
    # Check if the file time is older than three months
    return file_time < three_months_ago


def get_whole_size(path):
    total, used, free = shutil.disk_usage(path)
    return {
        "total": total,
        "used": used,
        "free": free
    }


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB")
    i = int(math.floor(math.log(size_bytes, 1024)))  # Determine the size name index
    p = math.pow(1024, i)  # 1024 raised to the power of index
    s = round(size_bytes / p, 2)  # Calculate size in the chosen unit
    return f"{s} {size_name[i]}"


def get_directory_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            # Skip if it is a symbolic link
            if not os.path.islink(filepath):
                total_size += os.path.getsize(filepath)
    return total_size


def delete_directory(path):
    try:
        if DRY_RUN:
            print(f"Delete dry run: {path}")
        else:
            # shutil.rmtree(path)
            print(f"Directory '{path}' has been deleted successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")


def init_background_job():
    print(f"INTERVAL_MINUTE: {INTERVAL_MINUTE}")
    print(f"MOVIES_PATH: {MOVIES_PATH}")
    print(f"DRY_RUN: {DRY_RUN}")
    # Create an instance of BackgroundScheduler
    scheduler = BackgroundScheduler()

    # Schedule the daily_task to run every day at a specific time (e.g., 10:00 AM)
    # scheduler.add_job(start_scan, 'cron', hour=10, minute=0)

    # Schedule the minute_task to run every minute
    scheduler.add_job(start_scan, 'interval', minutes=INTERVAL_MINUTE)

    # Start the scheduler
    scheduler.start()

    # graceful shutdown
    # def shutdown_scheduler(signum, frame):
    #     print("Shutting down the scheduler...")
    #     scheduler.shutdown()
    #
    # # Register the signal handler for graceful shutdown
    # signal.signal(signal.SIGINT, shutdown_scheduler)
    # signal.signal(signal.SIGTERM, shutdown_scheduler)

    # keep alive
    # Wait for the scheduler to run
    # try:
    #     while scheduler.running:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     shutdown_scheduler(None, None)
    #


if __name__ == '__main__':
    init_background_job()
    app.run(use_reloader=True, debug=True, host='0.0.0.0', port=PORT, threaded=True)
