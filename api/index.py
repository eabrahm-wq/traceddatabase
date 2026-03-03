import sys, os
# Make root-level modules (traced_app, company_routes) importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from traced_app import app

# Vercel looks for `app` or `handler` as the WSGI entrypoint
handler = app
