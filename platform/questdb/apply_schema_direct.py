import requests
import os

QUESTDB_HOST = "http://localhost:9000"
EXEC_ENDPOINT = "/exec"
SCHEMA_FILE = "schema.sql"

def read_schema_file():
    if not os.path.exists(SCHEMA_FILE):
        print(f"❌ Schema file not found: {SCHEMA_FILE}")
        return []
    with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    statements = [s.strip() for s in content.split(';') if s.strip()]
    return statements

def execute_ddl(statements):
    print(f"📜 Executing {len(statements)} statements on {QUESTDB_HOST}...")
    for sql in statements:
        # Extract table name for logging
        table_name = "unknown"
        if "CREATE TABLE" in sql.upper():
            try:
                parts = sql.split('(')[0].split()
                table_name = parts[-1]
            except:
                pass
        
        print(f"DTO: {table_name}...", end=" ")
        try:
            r = requests.get(f"{QUESTDB_HOST}{EXEC_ENDPOINT}", params={'query': sql})
            if r.status_code == 200:
                print(f"✅ Executed")
            elif "table already exists" in r.text or "duplicates" in r.text:
                print(f"ℹ️  Exists")
            else:
                print(f"⚠️ Error: {r.text}")
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    stmts = read_schema_file()
    execute_ddl(stmts)
