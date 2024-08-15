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
# load env
from dotenv import load_dotenv

load_dotenv()

# Flask App setup____________________________________________________
static_dir = "../public"
app = Flask(__name__, static_folder=static_dir)
cors = CORS(app, origins="*")

# env
PORT = int(os.getenv(key='BACKEND_PORT', default=8888))
DATA_PATH = os.getenv(key='DATA_PATH', default="../data")
DATA_FILE = f"{DATA_PATH}/data.json"
ROOT_MEDIA_PATH = os.getenv(key='ROOT_MEDIA_PATH', default="/Users/sauravahmed/Documents")
MOVIES_PATH = os.getenv(key='MEDIA_PATH', default="/Users/sauravahmed/Documents")
TV_SHOWS_PATH = os.getenv(key='TV_SHOWS_PATH', default="/Users/sauravahmed/Documents")
INTERVAL_MINUTE = int(os.getenv(key='INTERVAL_MINUTE', default=1))
CRON_HOUR = int(os.getenv(key='CRON_HOUR', default=10))
DURATION_DAYS = int(os.getenv(key='DURATION_DAYS', default=30))
DRY_RUN = os.getenv(key='DRY_RUN', default=True)
DIR_LIST = os.getenv(key='DIR_LIST', default="")
SIZE_LIMIT = os.getenv(key='SIZE_LIMIT', default="")
DELETE_ON_TIME_LIMIT = os.getenv(key='DELETE_ON_TIME_LIMIT', default=False)
DELETE_ON_SIZE_LIMIT = os.getenv(key='DELETE_ON_SIZE_LIMIT', default=False)
FORCE_DELETE_ON_SIZE_LIMIT = os.getenv(key='FORCE_DELETE_ON_SIZE_LIMIT', default=False)

# Create an instance of BackgroundScheduler
scheduler = BackgroundScheduler()


# requests___________________________________________________________
@app.route('/status', methods=["GET"])
def status():
    print("status")
    return {
        "status": "running"
    }


@app.route('/api/start', methods=["GET"])
def start_scanner():
    print("Start scanning manually")
    # scheduler.add_job(start_scan, 'date', next_run_time=datetime.now(), max_instances=1)
    scheduler.add_job(start_scan, max_instances=1)
    return {
        "status": "running"
    }


@app.route('/api/data', methods=["GET"])
def get_data():
    print("get data")
    data = get_all_data_content()
    if data:
        return data
    else:
        return {}


@app.route('/api/dirs', methods=["GET"])
def get_dirs():
    print("get dirs")
    dirs = get_data_value_content('dirs')
    if dirs:
        return {"dirs": dirs}
    else:
        return {"dirs": []}


@app.route('/api/dirs', methods=["POST"])
def save_dirs():
    print("set dirs")
    data = request.get_json()
    dirs = data.get('dirs', [])

    res = save_data_content("dirs", dirs)
    return {"success": res}


# interval time
@app.route('/api/interval', methods=["GET"])
def get_interval():
    print("get interval")
    interval = get_data_value_content('interval')
    if interval:
        return {"interval": interval}
    else:
        return {"interval": -1}


@app.route('/api/interval', methods=["POST"])
def save_interval():
    print("set interval")
    data = request.get_json()
    interval = data.get('interval', -1)

    res = save_data_content("interval", interval)
    return {"success": res}


@app.route('/api/dryrun', methods=["GET"])
def is_dryrun():
    print("is_dryrun")
    dryrun = get_data_value_content('dryrun')
    if dryrun:
        return {"dryrun": dryrun}
    else:
        return {"dryrun": False}


@app.route('/api/dryrun', methods=["POST"])
def save_dryrun():
    print("save_dryrun")
    data = request.get_json()
    dryrun = data.get('dryrun', False)

    res = save_data_content("dryrun", dryrun)
    return {"success": res}


@app.route('/get_size_movies', methods=["GET"])
def get_movies_size():
    size = get_directory_size(MOVIES_PATH)
    human_readable_size = convert_bytes_to_readable_size(size)
    return {
        "size": human_readable_size
    }


@app.route('/get_size_tvshows', methods=["GET"])
def get_tvshows_size():
    size = get_directory_size(TV_SHOWS_PATH)
    human_readable_size = convert_bytes_to_readable_size(size)
    return {
        "size": human_readable_size
    }


@app.route('/get_whole_size', methods=["GET"])
def get_whole_size_():
    print("status")
    size = get_whole_size(ROOT_MEDIA_PATH)
    human_readable_size = convert_bytes_to_readable_size(size.get("free"))
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
def put_filelist(data):
    filename = f"{DATA_PATH}/files.json"
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Data successfully written to {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")


def get_all_data_content():
    try:
        with open(DATA_FILE, 'r') as file:
            content = file.read()
            content = json.loads(content)
            return content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_data_value_content(key):
    content = get_all_data_content()
    if content and content.get(key):
        return content.get(key)
    else:
        return None


def save_data_content(key, value):
    content = get_all_data_content()
    print(f"key: {key}, content: {content}")
    if not content:
        content = {}

    content[key] = value
    print(f"updated content: {content}")
    try:
        with open(DATA_FILE, 'w') as file:
            file.write(json.dumps(content))
            return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# background job____________________________________________________
def list_directories(path):
    try:
        # List all entries in the given path
        entries = os.listdir(path)
        # Filter out entries that are directories and get their full paths
        # directories = [os.path.join(path, entry) for entry in entries if os.path.isdir(os.path.join(path, entry))]
        # do not include hidden dirs
        directories = [
            os.path.join(path, entry)
            for entry in entries
            if os.path.isdir(os.path.join(path, entry)) and not entry.startswith('.')
        ]
        return directories
    except FileNotFoundError:
        return f"Path '{path}' does not exist."
    except PermissionError:
        return f"Permission denied for path '{path}'."


def get_last_modification_time(path):
    # Get the last modification time
    mod_time = os.path.getmtime(path)
    # Convert it to a readable format
    # readable_time = time.ctime(mod_time)
    # return readable_time
    return mod_time


def get_sorted_dirs(directories_):
    directories = []
    for directory in directories_:
        size = get_directory_size(directory)
        last_mod = get_last_modification_time(directory)
        readable_time = time.ctime(last_mod)
        readable_size = convert_bytes_to_readable_size(size)
        directories.append({
            "path": directory,
            "last_mod": last_mod,
            "readable_time": readable_time,
            "size": size,
            "readable_size": readable_size
        })

    sorted_list = sorted(directories, key=lambda x: x['last_mod'])
    return sorted_list


def force_delete_on_size_limit(parent_dir_path, directories_, size_limit):
    sorted_list = get_sorted_dirs(directories_)
    delete_list = []
    dir_size = get_directory_size(parent_dir_path)
    diff_size = dir_size - size_limit

    print(f"size_limit:{convert_bytes_to_readable_size(size_limit)}")
    print(f"dir_size:{convert_bytes_to_readable_size(dir_size)}")
    print(f"diff_size:{convert_bytes_to_readable_size(diff_size)}")
    append_event_logs(
        f"FORCE_DELETE:size_limit:{convert_bytes_to_readable_size(size_limit)}:dir_size:{convert_bytes_to_readable_size(dir_size)}diff_size:{convert_bytes_to_readable_size(diff_size)}")

    count_size = 0
    for item in sorted_list:
        if count_size < diff_size:
            item_size = item.get("size")
            count_size = item_size + count_size
            delete_list.append({"path": item.get("path"), "size": convert_bytes_to_readable_size(item_size)})
        else:
            continue

    print(f"delete_list: {delete_list}")

    for i in delete_list:
        delete_directory(i.get("path"), i.get("last_mod"), i.get("readable_size"), "FORCE_DELETE_ON_SIZE_LIMIT")


def delete_files_older_then_duration(directories, mode):
    deleted_dirs = []
    for directory in directories:
        last_mod = get_last_modification_time(directory)
        if is_older_than_duration_days(last_mod):
            # delete task
            size = get_directory_size(directory)
            human_readable_size = convert_bytes_to_readable_size(size)
            readable_time = convert_timestamp_to_human_readable(last_mod)

            delete_directory(directory, last_mod, human_readable_size, mode)
            deleted_dirs.append(directory)
            print(f"{directory}: update: {readable_time} : size: {human_readable_size}")
    return deleted_dirs


def scan_dir(dir_path, size_limit_):
    directories = list_directories(dir_path)
    if not isinstance(directories, list):
        print(directories)
        return

    directories_size = get_directory_size(dir_path)
    size_limit = convert_readable_to_bytes_size(size_limit_)
    size_exceed = directories_size > size_limit
    append_event_logs(f"SCAN:{dir_path} size: {convert_bytes_to_readable_size(directories_size)}")
    append_event_logs(f"SCAN:{dir_path} size limit: {size_limit_}")
    append_event_logs(f"SCAN:{dir_path} size exceed: {size_exceed}")

    # delete if time limit exceed , no need to worry about DELETE_ON_SIZE_LIMIT and FORCE_DELETE_ON_SIZE_LIMIT
    if DELETE_ON_TIME_LIMIT:
        append_event_logs(f"DELETE_ON_TIME_LIMIT:start scanning:{dir_path}")
        delete_files_older_then_duration(directories, "DELETE_ON_TIME_LIMIT")
        return

    # do nothing if DELETE_ON_SIZE_LIMIT is false
    if size_exceed and not DELETE_ON_SIZE_LIMIT:
        return

    # delete files that older than duration if DELETE_ON_SIZE_LIMIT is true
    if size_exceed and DELETE_ON_SIZE_LIMIT:
        append_event_logs(f"DELETE_ON_SIZE_LIMIT:start scanning:{dir_path}")
        delete_files_older_then_duration(directories, "DELETE_ON_SIZE_LIMIT")
        return

    # check if anything get delete on DELETE_ON_SIZE_LIMIT because it may not if nothing is older then duration limit
    # delete oldest files if size exceeds even if time duration did not exceed
    if FORCE_DELETE_ON_SIZE_LIMIT and size_exceed:
        append_event_logs(f"FORCE_DELETE_ON_SIZE_LIMIT:start scanning:{dir_path}")
        append_event_logs(f"FORCE_DELETE_ON_SIZE_LIMIT:start scanning:{dir_path}")
        force_delete_on_size_limit(dir_path, directories, size_limit)
        return


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


def convert_readable_to_bytes_size(readable_size):
    if readable_size is None:
        return 0
    units = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3, "TB": 1024 ** 4, "PB": 1024 ** 5}
    readable_size = readable_size.upper().strip()

    # Extract the numerical part and the unit
    number = float(''.join([c for c in readable_size if c.isdigit() or c == '.']))
    unit = ''.join([c for c in readable_size if c.isalpha()]) or "B"

    if unit in units:
        return int(number * units[unit])
    else:
        raise ValueError(f"Unknown unit: {unit}")


def convert_bytes_to_readable_size(size_bytes):
    if size_bytes <= 0:
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


def delete_directory(path, last_mod, human_readable_size, mode):
    try:
        if DRY_RUN:
            print(f"Delete dry run: {path}")
        else:
            # shutil.rmtree(path)
            print(f"Directory '{path}' has been deleted successfully.")
        append_delete_logs(path, last_mod, human_readable_size, DRY_RUN, mode)
    except Exception as e:
        print(f"An error occurred: {e}")


def get_current_date_human_readable(include_hour=False):
    now = datetime.now()
    if include_hour:
        formatted_date_time = now.strftime("%d %B %Y %I:%M %p")
        return formatted_date_time
    else:
        formatted_date = now.strftime("%d %B %Y")
        formatted_date_time = now.strftime("%d %B %Y %I:%M %p")
        return formatted_date


def convert_timestamp_to_human_readable(timestamp):
    dt_object = datetime.fromtimestamp(timestamp)
    formatted_date_time = dt_object.strftime("%d %B %Y %I:%M %p")
    return formatted_date_time


def append_delete_logs(path, last_mod, human_readable_size, dry_run, mode):
    current_time = get_current_date_human_readable(True)
    log_file_path = f"{DATA_PATH}/{get_current_date_human_readable()}.log"
    if dry_run:
        content = f"{current_time}:{mode}: DRY RUN : {path}: {last_mod}: {human_readable_size}\n"
    else:
        content = f"{current_time}:{mode}: {path}: {last_mod}: {human_readable_size}\n"
    with open(log_file_path, 'a') as file:
        file.write(content)


def append_event_logs(event):
    current_time = get_current_date_human_readable(True)
    log_file_path = f"{DATA_PATH}/{get_current_date_human_readable()}.log"
    content = f"{current_time}:EVENT:{event}\n"
    with open(log_file_path, 'a') as file:
        file.write(content)


def get_size_limit(index):
    size_limits = SIZE_LIMIT.split(",")
    if index < len(size_limits):
        return size_limits[index]
    else:
        return None


def start_scan():
    print("START SCAN")
    append_event_logs("START_BACKGROUND_JOB")
    for index, path in enumerate(DIR_LIST.split(",")):
        if os.path.isdir(path):
            size_limit = get_size_limit(index)
            print("_" * 20)
            print(f"scanning path: {path}, size limit: {size_limit}")
            append_event_logs(f"START_SCAN: scanning path: {path}, size limit: {size_limit}")
            scan_dir(path, size_limit)
            print("_" * 20)
        else:
            print(f"invalid path: {path}")
    print("END SCAN")


def init_background_job():
    print("Reading environment variables")
    print(f"INTERVAL_MINUTE: {INTERVAL_MINUTE}")
    print(f"MOVIES_PATH: {MOVIES_PATH}")
    print(f"TV_SHOWS_PATH: {TV_SHOWS_PATH}")
    print(f"INTERVAL_MINUTE: {INTERVAL_MINUTE}")
    print(f"DURATION_DAYS: {DURATION_DAYS}")
    print(f"ROOT_MEDIA_PATH: {MOVIES_PATH}")
    print(f"DIR_LIST: {DIR_LIST}")
    print(f"DRY_RUN: {DRY_RUN}")
    print("_" * 10)

    # Schedule the daily_task to run every day at a specific time (e.g., 10:00 AM)
    # scheduler.add_job(start_scan, 'cron', hour=10, minute=0)

    # Schedule the minute_task to run every minute
    # scheduler.add_job(start_scan, 'interval', minutes=INTERVAL_MINUTE)
    scheduler.add_job(start_scan, 'interval', minutes=INTERVAL_MINUTE, next_run_time=datetime.now(), max_instances=1)

    # Start the scheduler
    print("start scheduler")
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
    append_event_logs("START_SERVER")
    app.run(use_reloader=False, debug=True, host='0.0.0.0', port=PORT, threaded=True)
