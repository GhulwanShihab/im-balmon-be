
import sys
import os
import json
from sqlalchemy import create_engine, text
from sqlmodel import Session

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings

def verify_data():
    input_file = os.path.join(os.path.dirname(__file__), "..", "data_backup.json")
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, "r") as f:
        data = json.load(f)

    print(f"Verifying migration to {settings.DATABASE_URI}...")
    engine = create_engine(str(settings.DATABASE_URI))

    tables = [
        "devices", "device_loans", "device_loan_items"
    ]
    
    mapping = {
        "devices": "devices",
        "device_loans": "device_loans",
        "device_loan_items": "device_loan_items"
    }

    all_match = True
    
    output = []
    with Session(engine) as session:
        for json_key, table_name in mapping.items():
            json_count = len(data.get(json_key, []))
            
            try:
                result = session.exec(text(f"SELECT COUNT(*) FROM {table_name}"))
                db_count = result.scalar()
            except Exception as e:
                msg = f"Error counting {table_name}: {e}"
                print(msg)
                output.append(msg)
                all_match = False
                continue
            
            if json_count == db_count:
                msg = f"✅ {table_name}: {db_count} rows (Match)"
                print(msg)
                output.append(msg)
            else:
                msg = f"❌ {table_name}: DB={db_count}, JSON={json_count} (MISMATCH)"
                print(msg)
                output.append(msg)
                all_match = False

    if all_match:
        final_msg = "\nSUCCESS: All table counts match!"
    else:
        final_msg = "\nWARNING: Some table counts do not match."
    
    print(final_msg)
    output.append(final_msg)
    
    with open("verification_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    verify_data()
