
import sys
import os
import json
from sqlmodel import Session, select
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from enum import Enum

# Add parent directory to path to allow importing from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
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

def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Type {type(obj)} not serializable")

def export_data():
    data = {}
    
    with Session(engine) as session:
        # 1. Users
        print("Exporting Users...")
        users = session.exec(select(User)).all()
        data["users"] = [user.model_dump() for user in users]
        
        # 2. Locations
        print("Exporting Locations...")
        locations = session.exec(select(Location)).all()
        data["locations"] = [loc.model_dump() for loc in locations]
        
        # 3. Employees
        print("Exporting Employees...")
        employees = session.exec(select(Employee)).all()
        data["employees"] = [emp.model_dump() for emp in employees]
        
        # 4. Devices
        print("Exporting Devices...")
        devices = session.exec(select(Device)).all()
        data["devices"] = [device.model_dump() for device in devices]
        
        # 5. Device Children
        print("Exporting Device Children...")
        children = session.exec(select(DeviceChild)).all()
        data["device_children"] = [child.model_dump() for child in children]
        
        # 6. Device Groups
        print("Exporting Device Groups...")
        groups = session.exec(select(DeviceGroup)).all()
        data["device_groups"] = [group.model_dump() for group in groups]
        
        # 7. Device Group Items
        print("Exporting Device Group Items...")
        group_items = session.exec(select(DeviceGroupItem)).all()
        data["device_group_items"] = [item.model_dump() for item in group_items]
        
        # 8. Device Loans
        print("Exporting Device Loans...")
        loans = session.exec(select(DeviceLoan)).all()
        data["device_loans"] = [loan.model_dump() for loan in loans]
        
        # 9. Device Loan Items
        print("Exporting Device Loan Items...")
        loan_items = session.exec(select(DeviceLoanItem)).all()
        data["device_loan_items"] = [item.model_dump() for item in loan_items]
        
        # 10. Loan History
        print("Exporting Loan History...")
        history = session.exec(select(LoanHistory)).all()
        data["loan_history"] = [h.model_dump() for h in history]
        
        # 11. Device Condition Change Requests
        print("Exporting Condition Change Requests...")
        requests = session.exec(select(DeviceConditionChangeRequest)).all()
        data["condition_change_requests"] = [req.model_dump() for req in requests]

    output_file = os.path.join(os.path.dirname(__file__), "..", "data_backup.json")
    with open(output_file, "w") as f:
        json.dump(data, f, default=json_serializer, indent=2)
    
    print(f"Data exported successfully to {output_file}")

if __name__ == "__main__":
    export_data()
