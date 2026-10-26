# Paste this into your PythonAnywhere WSGI file (Web tab -> WSGI configuration file).
# Replace YOURUSERNAME with your PythonAnywhere username.
import sys
path = "/home/YOURUSERNAME/khusela/backend"
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application   # app.py loads backend/.env by itself
