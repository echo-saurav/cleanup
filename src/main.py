import time
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import signal
import os
import math
from datetime import datetime, timedelta

path = '/Users/sauravahmed/Documents'


def start_scan():
    print("start scanning")


def is_older_than_three_months(timestamp):
    # Convert the timestamp to a datetime object
    file_time = datetime.fromtimestamp(timestamp)
    # Get the current time
    current_time = datetime.now()
    # Calculate the time three months ago
    three_months_ago = current_time - timedelta(days=90)  # Approximate 3 months as 90 days
    # Check if the file time is older than three months
    return file_time < three_months_ago


def get_last_modification_time(path):
    # Get the last modification time
    mod_time = os.path.getmtime(path)
    # Convert it to a readable format
    # readable_time = time.ctime(mod_time)
    # return readable_time
    return mod_time


def get_directory_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            # Skip if it is a symbolic link
            if not os.path.islink(filepath):
                total_size += os.path.getsize(filepath)
    return total_size


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB")
    i = int(math.floor(math.log(size_bytes, 1024)))  # Determine the size name index
    p = math.pow(1024, i)  # 1024 raised to the power of index
    s = round(size_bytes / p, 2)  # Calculate size in the chosen unit
    return f"{s} {size_name[i]}"


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


def old_init():
    directories = list_directories(path)
    if isinstance(directories, list):
        print(f"Directories in '{path}':")
        for directory in directories:
            print(f"{directory}: update: {get_last_modification_time(directory)}")

        print("# Three month old dir:")
        for directory in directories:
            last_mod = get_last_modification_time(directory)
            if is_older_than_three_months(last_mod):
                size = get_directory_size(directory)
                human_readable_size = convert_size(size)
                print(f"{directory}: update: {get_last_modification_time(directory)} : size: {human_readable_size}")

    else:
        print(directories)


# Graceful shutdown function


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


def init():
    init_background_job()
    # periodic run
    # check storage of dir
    # get all old files
    # delete old files


init()
