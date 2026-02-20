
import sys
import os
import json
from sqlalchemy import create_engine
from sqlmodel import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings
from src.models.loan import DeviceLoanItem

engine = create_engine(str(settings.DATABASE_URI))

def debug_items():
    input_file = os.path.join(os.path.dirname(__file__), "..", "data_backup.json")
    with open(input_file, "r") as f:
        data = json.load(f)

    print("Debugging Device Loan Items...")
    with Session(engine) as session:
        for item in data.get("device_loan_items", []):
            existing = session.get(DeviceLoanItem, item["id"])
            if not existing:
                try:
                    obj = DeviceLoanItem.model_validate(item)
                    session.add(obj)
                    session.commit()
                    print(f"Added item {item['id']}")
                except Exception as e:
                    msg = str(e)
                    # Extract detail from IntegrityError if possible
                    if "DETAIL:" in msg:
                        detail = msg.split("DETAIL:")[1].split("\n")[0]
                        print(f"Failed item {item['id']}: DETAIL: {detail}")
                    else:
                        print(f"Failed item {item['id']}: {msg[:200]}")
                    session.rollback()

if __name__ == "__main__":
    debug_items()
