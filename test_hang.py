import faulthandler
import threading
import sys
import os

faulthandler.enable()

def dump():
    print("Dumping traceback due to timeout!")
    faulthandler.dump_traceback(sys.stderr)
    os._exit(1)

timer = threading.Timer(15, dump)
timer.start()

sys.path.insert(0, os.path.abspath("."))
os.environ["DJANGO_SETTINGS_MODULE"] = "backend.settings"
import django
django.setup()
print("Django setup complete.")
from django.core.management import call_command
print("Calling migrate...")
call_command("migrate")
print("Migrate complete.")
timer.cancel()
