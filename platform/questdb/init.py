import requests
import time
import sys
import os

# Configuration
QUESTDB_HOST = os.environ.get("QUESTDB_HOST", "http://questdb:9000")
EXEC_ENDPOINT = "/exec"
SCHEMA_FILE = "schema.sql"

def wait_for_questdb():
    print(f"⏳ Connecting to QuestDB at {QUESTDB_HOST}...", flush=True)
    retries = 30
    while retries > 0:
        try:
            r = requests.get(f"{QUESTDB_HOST}/status")
            if r.status_code == 200:
                print("✅ QuestDB Online.", flush=True)
                return True
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
             print(f"⚠️ Connection warning: {e}", flush=True)
        time.sleep(2)
        retries -= 1
    print("❌ Failed to connect to QuestDB after multiple retries.", flush=True)
    sys.exit(1)

def read_schema_file():
    if not os.path.exists(SCHEMA_FILE):
        print(f"❌ Schema file not found at: {os.path.abspath(SCHEMA_FILE)}", flush=True)
        sys.exit(1)
        
    try:
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        # Split by semicolon to get individual statements, filtering empty ones
        statements = [s.strip() for s in content.split(';') if s.strip()]
        return statements
    except Exception as e:
        print(f"❌ Error reading schema file: {e}", flush=True)
        sys.exit(1)

def execute_ddl(statements):
    print(f"📜 Found {len(statements)} statements to execute.", flush=True)
    for sql in statements:
        # Extract table name for logging (naive approach)
        table_name = "unknown"
        if "CREATE TABLE" in sql.upper():
            try:
                # schema: CREATE TABLE IF NOT EXISTS assets (
                parts = sql.split('(')[0].split()
                table_name = parts[-1]
            except:
                pass
        
        print(f"DTO: Executing create for {table_name}...", flush=True)
        params = {'query': sql}
        try:
            r = requests.get(f"{QUESTDB_HOST}{EXEC_ENDPOINT}", params=params)
            if r.status_code == 200:
                print(f"✅ Executed: {table_name}", flush=True)
            elif "table already exists" in r.text or "duplicates" in r.text:
                 print(f"ℹ️  Exists: {table_name}", flush=True)
            else:
                print(f"⚠️ Error on {table_name}: {r.text}", flush=True)
        except Exception as e:
            print(f"❌ Critical Error executing SQL: {e}", flush=True)

def verify_tables():
    print("🔍 Verifying existing tables...", flush=True)
    try:
        r = requests.get(f"{QUESTDB_HOST}{EXEC_ENDPOINT}", params={'query': 'show tables'})
        if r.status_code == 200:
            data = r.json()
            if 'dataset' in data:
                tables = [row[0] for row in data['dataset']]
                print(f"📊 Current Tables in DB: {tables}", flush=True)
            else:
                print("⚠️ No dataset returned from info request.", flush=True)
        else:
            print(f"⚠️ Could not list tables: {r.text}", flush=True)
    except Exception as e:
        print(f"⚠️ Verification failed: {e}", flush=True)

if __name__ == "__main__":
    print(f"🚀 Starting Schema Init from {os.getcwd()}", flush=True)
    wait_for_questdb()
    statements = read_schema_file()
    execute_ddl(statements)
    verify_tables()
    print("🏁 Schema Initialization Process Complete.", flush=True)
