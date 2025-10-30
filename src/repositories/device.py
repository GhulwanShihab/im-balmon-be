"""Device repository for database operations."""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, update, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from src.models.perangkat import Device, DeviceStatus
from src.models.device_child import DeviceChild
from src.models.loan import DeviceCondition
from src.schemas.device import DeviceCreate, DeviceUpdate
import os

def no_deleted_filter(query):
    """Remove any deleted_at filter safely (for hard delete mode)."""
    return query

class DeviceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, device_id: int):
        """Get device or device_child by ID."""
        print(f"🔍 [DeviceRepo] mencari device_id={device_id}")

        # Cari di tabel devices dulu
        query_device = select(Device).where(Device.id == device_id)
        result_device = await self.session.execute(query_device)
        device = result_device.scalar_one_or_none()

        if device:
            print(f"✅ [DeviceRepo] ditemukan di devices: {device.device_name}")
            return device

        # Kalau tidak ada, cek di tabel device_children
        query_child = select(DeviceChild).where(DeviceChild.id == device_id)
        result_child = await self.session.execute(query_child)
        child = result_child.scalar_one_or_none()

        if child:
            print(f"✅ [DeviceRepo] ditemukan di device_children: {child.device_name}")
            return child

        print("❌ [DeviceRepo] tidak ditemukan di devices maupun device_children")
        return None

    async def get_by_code(self, device_code: str) -> Optional[Device]:
        """Get device by code."""
        query = select(Device).where(Device.device_code == device_code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_nup(self, nup_device: str) -> Optional[Device]:
        """Get device by NUP."""
        query = select(Device).where(Device.nup_device == nup_device)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, device_data: DeviceCreate) -> Device:
        """Create a new device."""
        device = Device(
            device_name=device_data.device_name,
            device_code=device_data.device_code,
            nup_device=device_data.nup_device,
            bmn_brand=device_data.bmn_brand,
            sample_brand=device_data.sample_brand,
            device_year=device_data.device_year,
            device_type=device_data.device_type,
            device_station=device_data.device_station,
            device_condition=device_data.device_condition,
            device_status=device_data.device_status,
            description=device_data.description,
            device_room=device_data.device_room,
            photos_url=device_data.photos_url or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(device)
        await self.session.commit()
        await self.session.refresh(device)
        return device

    async def update(self, device_id: int, device_data) -> Optional[Device]:
        device = await self.get_by_id(device_id)
        if not device:
            return None

        if isinstance(device_data, dict):
            update_data = device_data
        else:
            update_data = device_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():

            # ✅ khusus device_condition → konversi ke Enum
            if key == "device_condition":
                if isinstance(value, str):
                    try:
                        value = DeviceCondition(value)  # ✅ convert string ke enum
                    except ValueError:
                        print("❌ Invalid condition string:", value)
                        continue

                setattr(device, key, value)  # set enum, bukan string
                continue

            # ✅ JSON
            if key == "photos_url":
                setattr(device, key, value)
                flag_modified(device, "photos_url")
                continue

            setattr(device, key, value)

        device.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(device)
        print("🔧 Before:", device.device_condition)
        print("➡ New:", update_data.get("device_condition"))
        return device

    async def delete(self, device_id: int) -> bool:
        """Hard delete device: hapus dari DB dan hapus semua foto fisik."""
        device = await self.get_by_id(device_id)
        if not device:
            return False

        # 🧹 Hapus file foto jika ada
        if device.photos_url:
            for path in device.photos_url:
                abs_path = os.path.join(os.getcwd(), path.lstrip("/"))
                if os.path.exists(abs_path):
                    os.remove(abs_path)

        # 🧨 Hapus device dari database (bukan soft delete)
        await self.session.delete(device)
        await self.session.commit()
        return True

    async def get_all(self, skip: int = 0, limit: int = 10, filters: dict = None, sort_by: str = "created_at", sort_order: str = "desc") -> List[Device]:
        """Get all devices with pagination and filtering."""
        query = select(Device).options(selectinload(Device.children))
        
        # Apply filters
        if filters:
            if filters.get("device_name"):
                query = query.where(Device.device_name.ilike(f"%{filters['device_name']}%"))
            if filters.get("device_code"):
                query = query.where(Device.device_code.ilike(f"%{filters['device_code']}%"))
            if filters.get("nup_device"):
                query = query.where(Device.nup_device.ilike(f"%{filters['nup_device']}%"))
            if filters.get("bmn_brand"):
                query = query.where(Device.bmn_brand.ilike(f"%{filters['bmn_brand']}%"))
            if filters.get("sample_brand"):
                query = query.where(Device.sample_brand.ilike(f"%{filters['sample_brand']}%"))
            if filters.get("device_year"):
                query = query.where(Device.device_year == filters["device_year"])
            if filters.get("device_type"):
                query = query.where(Device.device_type.ilike(f"%{filters['device_type']}%"))
            if filters.get("device_station"):
                query = query.where(Device.device_station.ilike(f"%{filters['device_station']}%"))
            if filters.get("device_condition"):
                query = query.where(Device.device_condition == filters["device_condition"])
            if filters.get("device_status"):
                query = query.where(Device.device_status == filters["device_status"])
            if filters.get("device_room"):
                query = query.where(Device.device_room.ilike(f"%{filters['device_room']}%"))
        
        # Apply sorting
        if hasattr(Device, sort_by):
            if sort_order == "desc":
                query = query.order_by(getattr(Device, sort_by).desc())
            else:
                query = query.order_by(getattr(Device, sort_by))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def count(self, filters: dict = None) -> int:
        """Count total devices with filters."""
        query = select(func.count(Device.id))
        
        # Apply filters
        if filters:
            if filters.get("device_name"):
                query = query.where(Device.device_name.ilike(f"%{filters['device_name']}%"))
            if filters.get("device_code"):
                query = query.where(Device.device_code.ilike(f"%{filters['device_code']}%"))
            if filters.get("nup_device"):
                query = query.where(Device.nup_device.ilike(f"%{filters['nup_device']}%"))
            if filters.get("bmn_brand"):
                query = query.where(Device.bmn_brand.ilike(f"%{filters['bmn_brand']}%"))
            if filters.get("sample_brand"):
                query = query.where(Device.sample_brand.ilike(f"%{filters['sample_brand']}%"))
            if filters.get("device_year"):
                query = query.where(Device.device_year == filters["device_year"])
            if filters.get("device_type"):
                query = query.where(Device.device_type.ilike(f"%{filters['device_type']}%"))
            if filters.get("device_station"):
                query = query.where(Device.device_station.ilike(f"%{filters['device_station']}%"))
            if filters.get("device_condition"):
                query = query.where(Device.device_condition == filters["device_condition"])
            if filters.get("device_status"):
                query = query.where(Device.device_status == filters["device_status"])
            if filters.get("device_room"):
                query = query.where(Device.device_room.ilike(f"%{filters['device_room']}%"))
        
        result = await self.session.execute(query)
        return result.scalar()

    async def get_stats(self) -> dict:
        """Get comprehensive device statistics."""
        # Total devices
        total_query = select(func.count(Device.id))
        total_result = await self.session.execute(total_query)
        total_devices = total_result.scalar()
        
        # Active devices (assuming 'Aktif' status means active)
        active_query = select(func.count(Device.id)).where(Device.device_status == DeviceStatus.TERSEDIA)
        active_result = await self.session.execute(active_query)
        active_devices = active_result.scalar()
        
        # Inactive devices
        inactive_devices = total_devices - active_devices
        
        # Devices by condition
        condition_query = select(Device.device_condition, func.count(Device.id)).group_by(Device.device_condition)
        condition_result = await self.session.execute(condition_query)
        devices_by_condition = {row[0] or "Unknown": row[1] for row in condition_result.fetchall()}
        
        # Devices by status
        status_query = select(Device.device_status, func.count(Device.id)).group_by(Device.device_status)
        status_result = await self.session.execute(status_query)
        devices_by_status = {row[0] or "Unknown": row[1] for row in status_result.fetchall()}
        
        # Devices by type
        type_query = select(Device.device_type, func.count(Device.id)).group_by(Device.device_type)
        type_result = await self.session.execute(type_query)
        devices_by_type = {row[0] or "Unknown": row[1] for row in type_result.fetchall()}
        
        # Devices by room
        room_query = select(Device.device_room, func.count(Device.id)).group_by(Device.device_room)
        room_result = await self.session.execute(room_query)
        devices_by_room = {row[0] or "Unknown": row[1] for row in room_result.fetchall()}
        
        # New devices statistics
        today = datetime.utcnow().date()
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        # New devices today
        today_query = select(func.count(Device.id)).where(func.date(Device.created_at) == today)
        today_result = await self.session.execute(today_query)
        new_devices_today = today_result.scalar()
        
        # New devices this week
        week_query = select(func.count(Device.id)).where(Device.created_at >= week_ago)
        week_result = await self.session.execute(week_query)
        new_devices_this_week = week_result.scalar()
        
        # New devices this month
        month_query = select(func.count(Device.id)).where(Device.created_at >= month_ago)
        month_result = await self.session.execute(month_query)
        new_devices_this_month = month_result.scalar()
        
        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "inactive_devices": inactive_devices,
            "devices_by_condition": devices_by_condition,
            "devices_by_status": devices_by_status,
            "devices_by_type": devices_by_type,
            "devices_by_room": devices_by_room,
            "new_devices_today": new_devices_today,
            "new_devices_this_week": new_devices_this_week,
            "new_devices_this_month": new_devices_this_month
        }

    async def update_condition(self, device_id: int, condition: DeviceCondition) -> Optional[Device]:
        """Update device condition (used after admin approval)."""
        device = await self.get_by_id(device_id)
        if not device:
            return None

        # pastikan enum-nya tersimpan sebagai string yang sesuai dengan kolom database
        device.device_condition = condition.value if isinstance(condition, DeviceCondition) else condition
        device.updated_at = datetime.utcnow()

        self.session.add(device)
        await self.session.commit()
        await self.session.refresh(device)
        return device

    async def update_child_condition(self, child_device_id: int, condition: DeviceCondition) -> Optional[DeviceChild]:
        """Update condition for device child (used after admin approval)."""
        print(f"🔧 [DeviceRepo] update_child_condition: child_device_id={child_device_id}, condition={condition}")

        # cari data child
        query = select(DeviceChild).where(DeviceChild.id == child_device_id)
        result = await self.session.execute(query)
        child = result.scalar_one_or_none()

        if not child:
            print("❌ [DeviceRepo] child device tidak ditemukan")
            return None

        # pastikan enum-nya tersimpan sebagai string
        child.device_condition = condition.value if isinstance(condition, DeviceCondition) else condition
        child.updated_at = datetime.utcnow()

        self.session.add(child)
        await self.session.commit()
        await self.session.refresh(child)

        print(f"✅ [DeviceRepo] child device {child.device_name} diperbarui ke kondisi {child.device_condition}")
        return child

    async def update_status(self, device_id: int, status: str) -> Optional[Device]:
        """Update device status."""
        device = await self.get_by_id(device_id)
        if not device:
            return None
        
        device.device_status = status
        device.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(device)
        return device

    async def search_devices(self, search_term: str, limit: int = 10) -> List[Device]:
        """Search devices by name, code, or NUP."""
        query = (
            select(Device)
            .where(
                (
                    Device.device_name.ilike(f"%{search_term}%")
                    | Device.device_code.ilike(f"%{search_term}%")
                    | Device.nup_device.ilike(f"%{search_term}%")
                )
            )
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_device_usage_statistics(self, filters: dict = None, skip: int = 0, limit: int = 20) -> tuple:
        """Get detailed device usage statistics."""
        from ..models.loan import DeviceLoan, DeviceLoanItem, LoanStatus
        
        # Base query for device usage statistics
        base_query = """
        SELECT 
            d.id as device_id,
            d.nup_device,
            d.device_name,
            COALESCE(d.bmn_brand, d.sample_brand) as device_brand,
            d.device_year,
            d.device_condition,
            d.device_status,
            COALESCE(usage_stats.total_usage_days, 0) as total_usage_days,
            COALESCE(usage_stats.total_loans, 0) as total_loans,
            usage_stats.last_used_date,
            usage_stats.last_borrower,
            usage_stats.last_activity,
            CASE 
                WHEN usage_stats.total_loans > 0 
                THEN ROUND(usage_stats.total_usage_days::numeric / usage_stats.total_loans::numeric, 2)
                ELSE 0 
            END as average_usage_per_loan,
            CASE 
                WHEN usage_stats.total_loans = 0 THEN 0
                WHEN usage_stats.total_loans >= 20 THEN 100
                ELSE ROUND((usage_stats.total_loans::numeric / 20::numeric) * 100, 1)
            END as usage_frequency_score
        FROM devices d
        LEFT JOIN (
            SELECT 
                dli.device_id,
                SUM(dl.usage_duration_days * dli.quantity) as total_usage_days,
                COUNT(DISTINCT dl.id) as total_loans,
                MAX(dl.loan_end_date) as last_used_date,
                MAX(dl.borrower_name) FILTER (WHERE dl.loan_end_date = MAX(dl.loan_end_date) OVER (PARTITION BY dli.device_id)) as last_borrower,
                MAX(dl.activity_name) FILTER (WHERE dl.loan_end_date = MAX(dl.loan_end_date) OVER (PARTITION BY dli.device_id)) as last_activity
            FROM device_loan_items dli
            JOIN device_loans dl ON dli.loan_id = dl.id
            WHERE dl.deleted_at IS NULL 
                AND dl.status IN ('RETURNED', 'OVERDUE', 'ACTIVE')
            GROUP BY dli.device_id
        ) usage_stats ON d.id = usage_stats.device_id
        WHERE d.deleted_at IS NULL
        """
        
        # Add filters
        filter_conditions = []
        params = {}
        
        if filters:
            if filters.get("device_name"):
                filter_conditions.append("d.device_name ILIKE :device_name")
                params["device_name"] = f"%{filters['device_name']}%"
            
            if filters.get("nup_device"):
                filter_conditions.append("d.nup_device ILIKE :nup_device")
                params["nup_device"] = f"%{filters['nup_device']}%"
            
            if filters.get("device_brand"):
                filter_conditions.append("(d.bmn_brand ILIKE :device_brand OR d.sample_brand ILIKE :device_brand)")
                params["device_brand"] = f"%{filters['device_brand']}%"
            
            if filters.get("device_year"):
                filter_conditions.append("d.device_year = :device_year")
                params["device_year"] = filters["device_year"]
            
            if filters.get("device_condition"):
                filter_conditions.append("d.device_condition = :device_condition")
                params["device_condition"] = filters["device_condition"]
            
            if filters.get("device_status"):
                filter_conditions.append("d.device_status = :device_status")
                params["device_status"] = filters["device_status"]
            
            if filters.get("min_usage_days") is not None:
                filter_conditions.append("COALESCE(usage_stats.total_usage_days, 0) >= :min_usage_days")
                params["min_usage_days"] = filters["min_usage_days"]
            
            if filters.get("max_usage_days") is not None:
                filter_conditions.append("COALESCE(usage_stats.total_usage_days, 0) <= :max_usage_days")
                params["max_usage_days"] = filters["max_usage_days"]
            
            if filters.get("min_loans") is not None:
                filter_conditions.append("COALESCE(usage_stats.total_loans, 0) >= :min_loans")
                params["min_loans"] = filters["min_loans"]
            
            if filters.get("last_used_from"):
                filter_conditions.append("usage_stats.last_used_date >= :last_used_from")
                params["last_used_from"] = filters["last_used_from"]
            
            if filters.get("last_used_to"):
                filter_conditions.append("usage_stats.last_used_date <= :last_used_to")
                params["last_used_to"] = filters["last_used_to"]
        
        if filter_conditions:
            base_query += " AND " + " AND ".join(filter_conditions)
        
        # Count query
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as counted"
        count_result = await self.session.execute(count_query, params)
        total = count_result.scalar()
        
        # Add sorting and pagination
        sort_by = filters.get("sort_by", "total_usage_days") if filters else "total_usage_days"
        sort_order = filters.get("sort_order", "desc") if filters else "desc"
        
        # Map sort fields to actual column names
        sort_mapping = {
            "total_usage_days": "total_usage_days",
            "total_loans": "total_loans",
            "last_used_date": "last_used_date",
            "device_name": "d.device_name",
            "nup_device": "d.nup_device",
            "device_year": "d.device_year",
            "usage_frequency_score": "usage_frequency_score"
        }
        
        actual_sort_field = sort_mapping.get(sort_by, "total_usage_days")
        
        base_query += f" ORDER BY {actual_sort_field} {sort_order.upper()}"
        base_query += f" LIMIT {limit} OFFSET {skip}"
        
        # Execute main query
        result = await self.session.execute(base_query, params)
        devices_data = result.fetchall()
        
        return devices_data, total

    async def get_device_usage_summary(self) -> dict:
        """Get device usage summary statistics."""
        from ..models.loan import DeviceLoan, DeviceLoanItem
        
        summary_query = """
        SELECT 
            COUNT(DISTINCT d.id) as total_devices,
            COUNT(DISTINCT CASE WHEN usage_stats.total_loans > 0 THEN d.id END) as devices_with_usage,
            COUNT(DISTINCT CASE WHEN usage_stats.total_loans = 0 OR usage_stats.total_loans IS NULL THEN d.id END) as devices_never_used,
            COALESCE(SUM(usage_stats.total_usage_days), 0) as total_usage_days_all,
            ROUND(AVG(COALESCE(usage_stats.total_usage_days, 0)), 2) as average_usage_per_device
        FROM devices d
        LEFT JOIN (
            SELECT 
                dli.device_id,
                SUM(dl.usage_duration_days * dli.quantity) as total_usage_days,
                COUNT(DISTINCT dl.id) as total_loans
            FROM device_loan_items dli
            JOIN device_loans dl ON dli.loan_id = dl.id
            WHERE dl.deleted_at IS NULL 
                AND dl.status IN ('RETURNED', 'OVERDUE', 'ACTIVE')
            GROUP BY dli.device_id
        ) usage_stats ON d.id = usage_stats.device_id
        WHERE d.deleted_at IS NULL
        """
        
        result = await self.session.execute(summary_query)
        summary_data = result.fetchone()
        
        # Get most and least used devices
        most_used_query = """
        SELECT d.device_name, d.nup_device, usage_stats.total_usage_days, usage_stats.total_loans
        FROM devices d
        JOIN (
            SELECT 
                dli.device_id,
                SUM(dl.usage_duration_days * dli.quantity) as total_usage_days,
                COUNT(DISTINCT dl.id) as total_loans
            FROM device_loan_items dli
            JOIN device_loans dl ON dli.loan_id = dl.id
            WHERE dl.deleted_at IS NULL 
                AND dl.status IN ('RETURNED', 'OVERDUE', 'ACTIVE')
            GROUP BY dli.device_id
        ) usage_stats ON d.id = usage_stats.device_id
        WHERE d.deleted_at IS NULL
        ORDER BY usage_stats.total_usage_days DESC
        LIMIT 1
        """
        
        most_used_result = await self.session.execute(most_used_query)
        most_used = most_used_result.fetchone()
        
        # Get devices by condition
        condition_query = """
        SELECT device_condition, COUNT(*) as count
        FROM devices 
        WHERE deleted_at IS NULL
        GROUP BY device_condition
        """
        
        condition_result = await self.session.execute(condition_query)
        devices_by_condition = {row[0] or "Unknown": row[1] for row in condition_result.fetchall()}
        
        # Get devices by status
        status_query = """
        SELECT device_status, COUNT(*) as count
        FROM devices 
        WHERE deleted_at IS NULL
        GROUP BY device_status
        """
        
        status_result = await self.session.execute(status_query)
        devices_by_status = {row[0] or "Unknown": row[1] for row in status_result.fetchall()}
        
        # Get usage by year
        year_query = """
        SELECT d.device_year, COALESCE(SUM(usage_stats.total_usage_days), 0) as total_usage
        FROM devices d
        LEFT JOIN (
            SELECT 
                dli.device_id,
                SUM(dl.usage_duration_days * dli.quantity) as total_usage_days
            FROM device_loan_items dli
            JOIN device_loans dl ON dli.loan_id = dl.id
            WHERE dl.deleted_at IS NULL 
                AND dl.status IN ('RETURNED', 'OVERDUE', 'ACTIVE')
            GROUP BY dli.device_id
        ) usage_stats ON d.id = usage_stats.device_id
        WHERE d.deleted_at IS NULL AND d.device_year IS NOT NULL
        GROUP BY d.device_year
        ORDER BY d.device_year DESC
        """
        
        year_result = await self.session.execute(year_query)
        usage_by_year = {str(row[0]): int(row[1]) for row in year_result.fetchall()}
        
        return {
            "total_devices": summary_data[0],
            "devices_with_usage": summary_data[1],
            "devices_never_used": summary_data[2],
            "total_usage_days_all": int(summary_data[3]),
            "average_usage_per_device": float(summary_data[4]),
            "most_used_device": {
                "device_name": most_used[0],
                "nup_device": most_used[1],
                "total_usage_days": int(most_used[2]),
                "total_loans": int(most_used[3])
            } if most_used else None,
            "least_used_device": None,  # Could be implemented if needed
            "devices_by_condition": devices_by_condition,
            "devices_by_status": devices_by_status,
            "usage_by_year": usage_by_year
        }
    
    async def update_parent_status_based_on_children(self, parent_id: int):
        """Update parent status based on children statuses."""
        parent = await self.get_by_id(parent_id)
        if not parent:
            return None

        # Ambil semua children parent
        query = select(DeviceChild).where(DeviceChild.parent_id == parent_id)
        result = await self.session.execute(query)
        children = result.scalars().all()

        if not children:
            # kalau tidak ada child, biarkan status parent tetap
            return parent

        # Kalau ada minimal 1 child TERSEDIA, parent TERSEDIA
        if any(child.device_status == DeviceStatus.TERSEDIA for child in children):
            parent.device_status = DeviceStatus.TERSEDIA
        else:
            # Semua dipinjam/maintenance/nonaktif, parent DIPINJAM
            parent.device_status = DeviceStatus.DIPINJAM

        parent.updated_at = datetime.utcnow()
        self.session.add(parent)
        await self.session.commit()
        await self.session.refresh(parent)
        return parent