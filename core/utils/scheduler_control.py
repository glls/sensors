import threading
import time

import schedule

# Global variable to control the scheduler
scheduler_enabled = False


def periodic_task():
    print("Task executed")


def run_scheduler():
    while True:
        if scheduler_enabled:
            schedule.run_pending()
        time.sleep(1)


# Start the scheduler in a separate thread
threading.Thread(target=run_scheduler, daemon=True).start()
