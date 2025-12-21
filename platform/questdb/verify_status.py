import requests
import sys

HOST = "http://localhost:9000"

def run_query(query):
    try:
        r = requests.get(f"{HOST}/exec", params={'query': query})
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

def main():
    print(f"Checking QuestDB at {HOST}...")
    tables_data = run_query("show tables")
    
    if not tables_data or 'dataset' not in tables_data:
        print("❌ Could not list tables (or DB is empty).")
        return

    tables = [row[0] for row in tables_data['dataset']]
    print(f"✅ Found {len(tables)} tables: {', '.join(tables)}")
    
    print("\nTable Status:")
    print("-" * 30)
    for table in tables:
        count_data = run_query(f"select count() from '{table}'")
        count = -1
        if count_data and 'dataset' in count_data:
            count = count_data['dataset'][0][0]
        
        status = "🟢" if count >= 0 else "🔴"
        print(f"{status} {table:<15} Rows: {count}")

if __name__ == "__main__":
    main()
