import os
import time
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
PORT = os.getenv(key='BACKEND_PORT', default=8888)


# requests___________________________________________________________
@app.route('/home')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/home/<path:path>')
def send(path):
    return send_from_directory(app.static_folder, path)


@app.route('/info', methods=["POST"])
def info():
    data = request.get_json()

    start_book_id = data.get("start_book_id", None)
    res = {}
    response = Response(response=res, status=200, mimetype="application/json")
    return response


@app.route('/get_size', methods=["GET"])
def get_size():
    print("status")
    path = "/Users/sauravahmed/"
    size = get_directory_size(path)
    human_readable_size = convert_size(size)
    return {
        "size": human_readable_size
    }


@app.route('/get_whole_size', methods=["GET"])
def get_whole_size_():
    print("status")
    path = "/Users/sauravahmed/"
    size = get_whole_size(path)
    human_readable_size = convert_size(size.get("free"))
    return {
        "size": human_readable_size
    }


@app.route('/status', methods=["GET"])
def status():
    print("status")
    return {
        "status": "running"
    }


# store data____________________________________________________
def put_log(data):
    pass


# background job____________________________________________________

def start_scan():
    pass


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


def init_background_job():
    # Create an instance of BackgroundScheduler
    scheduler = BackgroundScheduler()

    # Schedule the daily_task to run every day at a specific time (e.g., 10:00 AM)
    # scheduler.add_job(start_scan, 'cron', hour=10, minute=0)

    # Schedule the minute_task to run every minute
    scheduler.add_job(start_scan, 'interval', minutes=1)

    # Start the scheduler
    scheduler.start()

    # graceful shutdown
    def shutdown_scheduler(signum, frame):
        print("Shutting down the scheduler...")
        scheduler.shutdown()

    # Register the signal handler for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_scheduler)
    signal.signal(signal.SIGTERM, shutdown_scheduler)

    # keep alive
    # Wait for the scheduler to run
    try:
        while scheduler.running:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown_scheduler(None, None)


if __name__ == '__main__':
    app.run(use_reloader=True, debug=True, host='0.0.0.0', port=PORT, threaded=True)
