from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from . import file_download


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(file_download.main, 'interval', hours=12)
    scheduler.start()
