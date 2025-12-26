import requests
from utils.config import Config

HOST = Config.QUESTDB_HOST
PORT = 9000
QUERY_URL = f"http://{HOST}:{PORT}/exec"

def run_query(q):
    r = requests.get(QUERY_URL, params={'query': q})
    print(f"Query: {q}")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
    print("-" * 20)

print("--- Checking Tables ---")
run_query("SHOW TABLES")

print("--- Checking Market Schema ---")
run_query("SHOW COLUMNS FROM market")

# Optional: Drop if it looks weird
# run_query("DROP TABLE market")
