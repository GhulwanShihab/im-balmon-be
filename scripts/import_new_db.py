
import sys
import os
import json
from sqlalchemy import create_engine, text
from sqlmodel import Session, select
from datetime import datetime

# Add parent directory to path to allow importing from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings
from src.models.user import User
from src.models.location import Location
from src.models.perangkat import Device
from src.models.device_child import DeviceChild
from src.models.device_group import DeviceGroup, DeviceGroupItem
from src.models.loan import DeviceLoan, DeviceLoanItem, LoanHistory, DeviceConditionChangeRequest
from src.models.employee import Employee

# Create sync engine
engine = create_engine(str(settings.DATABASE_URI))

def import_data():
    input_file = os.path.join(os.path.dirname(__file__), "..", "data_backup.json")
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, "r") as f:
        data = json.load(f)

    with Session(engine) as session:
        # Import Order matters due to Foreign Keys

        # 1. Users
        print("Importing Users...")
        for item in data.get("users", []):
            existing = session.get(User, item["id"])
            if not existing:
                obj = User.model_validate(item)
                session.add(obj)
        session.commit()
        print("Users committed.")

        # 2. Locations
        print("Importing Locations...")
        for item in data.get("locations", []):
            existing = session.get(Location, item["id"])
            if not existing:
                obj = Location.model_validate(item)
                session.add(obj)
                print(f"Added Location {item['id']}")
        session.commit()
        print("Locations committed.")

        # 3. Employees
        print("Importing Employees...")
        for item in data.get("employees", []):
            existing = session.get(Employee, item["id"])
            if not existing:
                obj = Employee.model_validate(item)
                session.add(obj)
                print(f"Added Employee {item['id']}")
        session.commit()
        print("Employees committed.")

        # 4. Devices
        print("Importing Devices...")
        for item in data.get("devices", []):
            existing = session.get(Device, item["id"])
            if not existing:
                try:
                    obj = Device.model_validate(item)
                    session.add(obj)
                    session.commit() # Commit individually to isolate
                    print(f"Added Device {item['id']}")
                except Exception as e:
                    print(f"Failed to add Device {item['id']}: {e}")
                    session.rollback()
        # session.commit() # Already committed line by line
        print("Devices committed.")

        # 5. Device Children
        print("Importing Device Children...")
        for item in data.get("device_children", []):
            existing = session.get(DeviceChild, item["id"])
            if not existing:
                try:
                    obj = DeviceChild.model_validate(item)
                    session.add(obj)
                    session.commit()
                    print(f"Added DeviceChild {item['id']}")
                except Exception as e:
                    print(f"Failed to add DeviceChild {item['id']}: {e}")
                    session.rollback()
        # session.commit()
        print("Device Children committed.")
        
        # 6. Device Groups
        print("Importing Device Groups...", flush=True)
        for item in data.get("device_groups", []):
            existing = session.get(DeviceGroup, item["id"])
            if not existing:
                try:
                    obj = DeviceGroup.model_validate(item)
                    session.add(obj)
                    session.commit()
                    print(f"Added DeviceGroup {item['id']}", flush=True)
                except Exception as e:
                    print(f"Failed to add DeviceGroup {item['id']}: {e}", flush=True)
                    session.rollback()
        print("Device Groups committed.", flush=True)

        # 7. Device Group Items
        print("Importing Device Group Items...", flush=True)
        for item in data.get("device_group_items", []):
            existing = session.get(DeviceGroupItem, item["id"])
            if not existing:
                try:
                    obj = DeviceGroupItem.model_validate(item)
                    # Ensure nulls are handled if needed
                    session.add(obj)
                    session.commit()
                    print(f"Added DeviceGroupItem {item['id']}", flush=True)
                except Exception as e:
                    print(f"Failed to add DeviceGroupItem {item['id']}: {e}", flush=True)
                    session.rollback()
        print("Device Group Items committed.", flush=True)

        # 8. Device Loans
        print("Importing Device Loans...", flush=True)
        for item in data.get("device_loans", []):
            existing = session.get(DeviceLoan, item["id"])
            if not existing:
                try:
                    obj = DeviceLoan.model_validate(item)
                    session.add(obj)
                    session.commit()
                    print(f"Added DeviceLoan {item['id']}", flush=True)
                except Exception as e:
                    print(f"Failed to add DeviceLoan {item['id']}: {e}", flush=True)
                    session.rollback()
        print("Device Loans committed.", flush=True)

        # 9. Device Loan Items
        print("Importing Device Loan Items...", flush=True)
        for item in data.get("device_loan_items", []):
            existing = session.get(DeviceLoanItem, item["id"])
            if not existing:
                try:
                    obj = DeviceLoanItem.model_validate(item)
                    
                    # Verify foreign keys existence
                    if obj.device_id:
                        if not session.get(Device, obj.device_id):
                            print(f"Warning: Device {obj.device_id} not found for Loan Item {item['id']}. Setting to None.", flush=True)
                            obj.device_id = None
                            
                    if obj.child_device_id:
                        if not session.get(DeviceChild, obj.child_device_id):
                            print(f"Warning: DeviceChild {obj.child_device_id} not found for Loan Item {item['id']}. Setting to None.", flush=True)
                            obj.child_device_id = None

                    session.add(obj)
                    session.commit()
                    print(f"Added DeviceLoanItem {item['id']}", flush=True)
                except Exception as e:
                    print(f"Failed to add DeviceLoanItem {item['id']}: {e}", flush=True)
                    session.rollback()
        print("Device Loan Items committed.", flush=True)

        # 10. Loan History
        print("Importing Loan History...", flush=True)
        for item in data.get("loan_history", []):
            existing = session.get(LoanHistory, item["id"])
            if not existing:
                try:
                    obj = LoanHistory.model_validate(item)
                    session.add(obj)
                    session.commit()
                    print(f"Added LoanHistory {item['id']}", flush=True)
                except Exception as e:
                    print(f"Failed to add LoanHistory {item['id']}: {e}", flush=True)
                    session.rollback()
        print("Loan History committed.", flush=True)

        # 11. Condition Change Requests
        print("Importing Condition Change Requests...", flush=True)
        for item in data.get("condition_change_requests", []):
            existing = session.get(DeviceConditionChangeRequest, item["id"])
            if not existing:
                try:
                    # model_validate might fail if related fields are missing or wrong type
                    # But export dump should correspond
                    obj = DeviceConditionChangeRequest.model_validate(item)
                    session.add(obj)
                    session.commit()
                    print(f"Added DeviceConditionChangeRequest {item['id']}", flush=True)
                except Exception as e:
                    print(f"Failed to add DeviceConditionChangeRequest {item['id']}: {e}", flush=True)
                    session.rollback()
        print("Condition Change Requests committed.", flush=True)

        # Reset Sequences
        print("Resetting sequences...")
        tables = [
            "users", "locations", "employees", "devices", "device_children",
            "device_groups", "device_group_items", "device_loans", "device_loan_items",
            "loan_history", "device_condition_change_requests"
        ]
        
        for table in tables:
            try:
                sql = text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id)+1, 1), false) FROM {table};")
                session.exec(sql)
            except Exception as e:
                print(f"Warning: Could not reset sequence for {table}: {e}")
        
    print("Data imported successfully!")

if __name__ == "__main__":
    try:
        import_data()
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stdout)
        print(f"Import failed: {e}")
