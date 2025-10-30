"""Device service for business logic."""

from typing import Optional
from fastapi import UploadFile, HTTPException, status
from datetime import datetime
import os

from src.repositories.device import DeviceRepository
from src.schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceListResponse,
    DeviceConditionUpdate, DeviceStatusUpdate, DeviceUsageStatistics,
    DeviceUsageFilter, DeviceUsageListResponse, DeviceUsageSummary
)

# ✅ Tambahkan ini di atas
# BASE_DIR mengarah ke root folder project (bukan src)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads", "devices")

class DeviceService:
    def __init__(self, device_repo: DeviceRepository):
        self.device_repo = device_repo

    async def create_device(self, device_data: DeviceCreate) -> DeviceResponse:
        """Create a new device with validation."""
        # Check if device code already exists
        existing_device = await self.device_repo.get_by_code(device_data.device_code)
        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device code already exists"
            )
        
        # Check if NUP already exists (only if provided)
        #if device_data.nup_device:
            #existing_nup = await self.device_repo.get_by_nup(device_data.nup_device)
            #if existing_nup:
                #raise HTTPException(
                    #status_code=status.HTTP_400_BAD_REQUEST,
                    #detail="NUP device already exists"
                #)
        
        # Create device
        device = await self.device_repo.create(device_data)
        return DeviceResponse.model_validate(device)

    async def get_device(self, device_id: int) -> Optional[DeviceResponse]:
        """Get device by ID."""
        device = await self.device_repo.get_by_id(device_id)
        print("DEBUG DEVICE PHOTOS_URL:", device.photos_url)
        if not device:
            return None
        
        return DeviceResponse.model_validate(device)

    async def get_device_by_code(self, device_code: str) -> Optional[DeviceResponse]:
        """Get device by code."""
        device = await self.device_repo.get_by_code(device_code)
        if not device:
            return None
        
        return DeviceResponse.model_validate(device)

    async def get_device_by_nup(self, nup_device: str) -> Optional[DeviceResponse]:
        """Get device by NUP."""
        device = await self.device_repo.get_by_nup(nup_device)
        if not device:
            return None
        
        return DeviceResponse.model_validate(device)

    async def get_all_devices(self, skip: int = 0, limit: int = 10, filters: dict = None, sort_by: str = "created_at", sort_order: str = "desc") -> DeviceListResponse:
        """Get all devices with pagination and filtering."""
        devices = await self.device_repo.get_all(skip, limit, filters, sort_by, sort_order)
        total = await self.device_repo.count(filters)
        
        device_responses = [DeviceResponse.model_validate(device) for device in devices]
        
        total_pages = (total + limit - 1) // limit
        page = (skip // limit) + 1
        
        return DeviceListResponse(
            devices=device_responses,
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages
        )

    async def update_device(self, device_id: int, device_data: DeviceUpdate) -> DeviceResponse:
        """Update device information."""
        # Check if device exists
        existing_device = await self.device_repo.get_by_id(device_id)
        if not existing_device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Check if device code is being updated and already exists
        if device_data.device_code and device_data.device_code != existing_device.device_code:
            existing_code = await self.device_repo.get_by_code(device_data.device_code)
            if existing_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Device code already exists"
                )
        
        #if device_data.nup_device and device_data.nup_device != existing_device.nup_device:
            #existing_nup = await self.device_repo.get_by_nup(device_data.nup_device)
            #if existing_nup:
                #raise HTTPException(
                    #status_code=status.HTTP_400_BAD_REQUEST,
                    #detail="NUP device already exists"
                #)

        device = await self.device_repo.update(device_id, device_data)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return DeviceResponse.model_validate(device)

    async def delete_device(self, device_id: int) -> bool:
        """Delete device (hard delete)."""
        success = await self.device_repo.delete(device_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        return success


    async def get_device_stats(self) -> dict:
        """Get device statistics."""
        return await self.device_repo.get_stats()

    async def update_device_condition(self, device_id: int, condition_data: DeviceConditionUpdate) -> DeviceResponse:
        """Update device condition."""
        device = await self.device_repo.update_condition(device_id, condition_data.device_condition)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return DeviceResponse.model_validate(device)

    async def update_device_status(self, device_id: int, status_data: DeviceStatusUpdate) -> DeviceResponse:
        """Update device status."""
        device = await self.device_repo.update_status(device_id, status_data.device_status)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return DeviceResponse.model_validate(device)

    async def search_devices(self, search_term: str, limit: int = 10) -> list[DeviceResponse]:
        """Search devices by name, code, or NUP."""
        devices = await self.device_repo.search_devices(search_term, limit)
        return [DeviceResponse.model_validate(device) for device in devices]

    async def get_devices_by_condition(self, condition: str, skip: int = 0, limit: int = 10) -> DeviceListResponse:
        """Get devices by condition."""
        filters = {"device_condition": condition}
        return await self.get_all_devices(skip, limit, filters)

    async def get_devices_by_status(self, status: str, skip: int = 0, limit: int = 10) -> DeviceListResponse:
        """Get devices by status."""
        filters = {"device_status": status}
        return await self.get_all_devices(skip, limit, filters)

    async def get_devices_by_room(self, room: str, skip: int = 0, limit: int = 10) -> DeviceListResponse:
        """Get devices by room."""
        filters = {"device_room": room}
        return await self.get_all_devices(skip, limit, filters)

    async def get_devices_by_type(self, device_type: str, skip: int = 0, limit: int = 10) -> DeviceListResponse:
        """Get devices by type."""
        filters = {"device_type": device_type}
        return await self.get_all_devices(skip, limit, filters)

    async def get_device_usage_statistics(self, usage_filter: DeviceUsageFilter) -> DeviceUsageListResponse:
        """Get device usage statistics with filtering and pagination."""
        
        # Convert filter object to dict for repository
        filters = {}
        if usage_filter.device_name:
            filters["device_name"] = usage_filter.device_name
        if usage_filter.nup_device:
            filters["nup_device"] = usage_filter.nup_device
        if usage_filter.device_brand:
            filters["device_brand"] = usage_filter.device_brand
        if usage_filter.device_year:
            filters["device_year"] = usage_filter.device_year
        if usage_filter.device_condition:
            filters["device_condition"] = usage_filter.device_condition
        if usage_filter.device_status:
            filters["device_status"] = usage_filter.device_status
        if usage_filter.min_usage_days is not None:
            filters["min_usage_days"] = usage_filter.min_usage_days
        if usage_filter.max_usage_days is not None:
            filters["max_usage_days"] = usage_filter.max_usage_days
        if usage_filter.min_loans is not None:
            filters["min_loans"] = usage_filter.min_loans
        if usage_filter.last_used_from:
            filters["last_used_from"] = usage_filter.last_used_from
        if usage_filter.last_used_to:
            filters["last_used_to"] = usage_filter.last_used_to
        
        filters["sort_by"] = usage_filter.sort_by
        filters["sort_order"] = usage_filter.sort_order
        
        # Calculate skip
        skip = (usage_filter.page - 1) * usage_filter.page_size
        
        # Get data from repository
        devices_data, total = await self.device_repo.get_device_usage_statistics(
            filters=filters, 
            skip=skip, 
            limit=usage_filter.page_size
        )
        
        # Convert to response objects
        devices_stats = []
        for row in devices_data:
            device_stat = DeviceUsageStatistics(
                device_id=row[0],
                nup_device=row[1],
                device_name=row[2],
                device_brand=row[3],
                device_year=row[4],
                device_condition=row[5],
                device_status=row[6],
                total_usage_days=row[7],
                total_loans=row[8],
                last_used_date=row[9],
                last_borrower=row[10],
                last_activity=row[11],
                average_usage_per_loan=float(row[12]) if row[12] else 0.0,
                usage_frequency_score=float(row[13]) if row[13] else 0.0
            )
            devices_stats.append(device_stat)
        
        # Get summary statistics
        summary = await self.device_repo.get_device_usage_summary()
        
        # Calculate total pages
        total_pages = (total + usage_filter.page_size - 1) // usage_filter.page_size
        
        return DeviceUsageListResponse(
            devices=devices_stats,
            total=total,
            page=usage_filter.page,
            page_size=usage_filter.page_size,
            total_pages=total_pages,
            summary=summary
        )

    async def get_device_usage_summary(self) -> DeviceUsageSummary:
        """Get device usage summary statistics."""
        summary_data = await self.device_repo.get_device_usage_summary()
        
        return DeviceUsageSummary(
            total_devices=summary_data["total_devices"],
            devices_with_usage=summary_data["devices_with_usage"],
            devices_never_used=summary_data["devices_never_used"],
            total_usage_days_all=summary_data["total_usage_days_all"],
            average_usage_per_device=summary_data["average_usage_per_device"],
            most_used_device=summary_data["most_used_device"],
            least_used_device=summary_data["least_used_device"],
            devices_by_condition=summary_data["devices_by_condition"],
            devices_by_status=summary_data["devices_by_status"],
            usage_by_year=summary_data["usage_by_year"]
        )

    async def get_never_used_devices(self) -> list[DeviceResponse]:
        """Get list of devices that have never been used in loans."""
        filters = {"min_loans": 0, "max_loans": 0}
        devices_data, _ = await self.device_repo.get_device_usage_statistics(
            filters=filters, 
            skip=0, 
            limit=1000
        )
        
        never_used_devices = []
        for row in devices_data:
            if row[8] == 0:  # total_loans is 0
                device = await self.device_repo.get_by_id(row[0])
                if device:
                    never_used_devices.append(DeviceResponse.model_validate(device))
        
        return never_used_devices

    async def get_most_used_devices(self, limit: int = 10) -> list[DeviceUsageStatistics]:
        """Get most used devices based on total usage days."""
        filters = {"sort_by": "total_usage_days", "sort_order": "desc"}
        devices_data, _ = await self.device_repo.get_device_usage_statistics(
            filters=filters, 
            skip=0, 
            limit=limit
        )
        
        most_used = []
        for row in devices_data:
            if row[7] > 0:  # total_usage_days > 0
                device_stat = DeviceUsageStatistics(
                    device_id=row[0],
                    nup_device=row[1],
                    device_name=row[2],
                    device_brand=row[3],
                    device_year=row[4],
                    device_condition=row[5],
                    device_status=row[6],
                    total_usage_days=row[7],
                    total_loans=row[8],
                    last_used_date=row[9],
                    last_borrower=row[10],
                    last_activity=row[11],
                    average_usage_per_loan=float(row[12]) if row[12] else 0.0,
                    usage_frequency_score=float(row[13]) if row[13] else 0.0
                )
                most_used.append(device_stat)
        return most_used
    
    async def upload_device_photo(self, device_id: int, file: UploadFile):
        """Upload foto perangkat dan ganti foto lama sepenuhnya."""
        device = await self.device_repo.get_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
    
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    
        # Validasi tipe file
        allowed_exts = [".jpg", ".jpeg", ".png", ".webp"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_exts:
            raise HTTPException(status_code=400, detail="Only JPG, PNG, and WEBP formats are allowed")
    
        # 🔥 Hapus semua foto lama sebelum upload baru
        if device.photos_url:
            for old_path in device.photos_url:
                abs_old_path = os.path.join(os.getcwd(), old_path.lstrip("/"))
                if os.path.exists(abs_old_path):
                    os.remove(abs_old_path)
    
        # Simpan dengan nama unik
        filename = f"{device.device_code}_{int(datetime.utcnow().timestamp())}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
    
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    
        # 🔁 Ganti dengan foto baru
        rel_path = f"/static/uploads/devices/{filename}"
        device.photos_url = [rel_path]  # <- replace total, bukan append
    
        # Update database
        from src.schemas.device import DeviceUpdate
        await self.device_repo.update(device_id, DeviceUpdate(photos_url=device.photos_url))
    
        # Ambil ulang device terbaru agar data return sudah update
        updated_device = await self.device_repo.get_by_id(device_id)
        return updated_device



    async def delete_device_photo(self, device_id: int, filename: str):
        """Hapus satu foto perangkat berdasarkan filename."""
        device = await self.device_repo.get_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        # Cari file di list photos_url
        if not device.photos_url:
            raise HTTPException(status_code=404, detail="No photos to delete")

        new_photos = []
        deleted_path = None
        for path in device.photos_url:
            if filename in path:
                deleted_path = path
            else:
                new_photos.append(path)

        if not deleted_path:
            raise HTTPException(status_code=404, detail="Photo not found")

        # Hapus file fisik
        abs_path = os.path.join(BASE_DIR, deleted_path.lstrip("/"))
        if os.path.exists(abs_path):
            os.remove(abs_path)

        # Update field photos_url di database
        device.photos_url = new_photos
        from src.schemas.device import DeviceUpdate
        await self.device_repo.update(device_id, DeviceUpdate(photos_url=device.photos_url))

        # ✅ Muat ulang device terbaru dari database agar response up to date
        updated_device = await self.device_repo.get_by_id(device_id)

        return updated_device


    async def get_device_photos(self, device_id: int):
        """Ambil semua foto dari perangkat tertentu."""
        device = await self.device_repo.get_by_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        return device.photos_url or []
        
        return most_used