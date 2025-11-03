"""Device Group service with business logic."""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from fastapi import HTTPException, status

from src.repositories.device_group import DeviceGroupRepository
from src.repositories.loan import LoanRepository
from src.repositories.device import DeviceRepository
from src.schemas.device_group import (
    DeviceGroupCreate, DeviceGroupUpdate, DeviceGroupResponse,
    DeviceGroupDetailResponse, DeviceGroupListResponse,
    DeviceGroupItemResponse, DeviceGroupAddDevices, 
    DeviceGroupRemoveDevices, DeviceGroupBorrowRequest,
    DeviceGroupBorrowResponse
)
from src.schemas.loan import DeviceLoanCreate, DeviceLoanItemBase, DeviceCondition
from src.models.perangkat import DeviceStatus
from src.models.loan import DeviceLoanItem


class DeviceGroupService:
    """Service for device group operations."""
    
    def __init__(
        self, 
        device_group_repo: DeviceGroupRepository,
        loan_repo: Optional[LoanRepository] = None,
        device_repo: Optional[DeviceRepository] = None
    ):
        self.device_group_repo = device_group_repo
        self.loan_repo = loan_repo
        self.device_repo = device_repo
    
    async def create_group(
        self, 
        group_data: DeviceGroupCreate, 
        user_id: int
    ) -> DeviceGroupDetailResponse:
        """Create a new device group."""
        # Create group
        group = await self.device_group_repo.create_group({
            "name": group_data.name,
            "description": group_data.description,
            "user_id": user_id
        })
        
        # Add devices if provided
        added_devices = []
        
        if group_data.device_ids:
            for device_id in group_data.device_ids:
                # Verify device exists
                device = await self.device_group_repo.get_device(device_id)
                if not device:
                    continue
                
                item = await self.device_group_repo.add_device_to_group(
                    group.id, 
                    device_id=device_id
                )
                if item:
                    added_devices.append(self._build_device_item_response(item, device))
        
        if group_data.child_device_ids:
            for child_id in group_data.child_device_ids:
                # Verify child device exists
                child = await self.device_group_repo.get_child_device(child_id)
                if not child:
                    continue
                
                item = await self.device_group_repo.add_device_to_group(
                    group.id, 
                    child_device_id=child_id
                )
                if item:
                    added_devices.append(self._build_device_item_response(item, child))
        
        # Check availability
        availability = await self.device_group_repo.check_group_devices_availability(group.id)
        
        return DeviceGroupDetailResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            user_id=group.user_id,
            created_at=group.created_at,
            updated_at=group.updated_at,
            device_count=len(added_devices),
            devices=added_devices,
            all_available=availability["all_available"],
            unavailable_devices=[d["name"] for d in availability["unavailable_devices"]]
        )
    
    async def get_group(self, group_id: int, user_id: int) -> DeviceGroupDetailResponse:
        """Get device group by ID."""
        group = await self.device_group_repo.get_group(group_id)
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device group not found"
            )
        
        # Check ownership
        if group.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get devices with details
        items = await self.device_group_repo.get_group_devices(group_id)
        device_responses = []
        
        for item in items:
            device = item.device if item.device_id else item.child_device
            if device:
                device_responses.append(self._build_device_item_response(item, device))
        
        # Check availability
        availability = await self.device_group_repo.check_group_devices_availability(group_id)
        
        return DeviceGroupDetailResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            user_id=group.user_id,
            created_at=group.created_at,
            updated_at=group.updated_at,
            device_count=len(device_responses),
            devices=device_responses,
            all_available=availability["all_available"],
            unavailable_devices=[d["name"] for d in availability["unavailable_devices"]]
        )
    
    async def get_user_groups(
        self, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20,
        name_filter: Optional[str] = None
    ) -> DeviceGroupListResponse:
        """Get all groups for a user."""
        skip = (page - 1) * page_size
        filters = {"name": name_filter} if name_filter else None
        
        groups, total = await self.device_group_repo.get_user_groups(
            user_id, skip, page_size, filters
        )
        
        group_responses = []
        for group in groups:
            device_count = len(group.group_items) if group.group_items else 0
            group_responses.append(
                DeviceGroupResponse(
                    id=group.id,
                    name=group.name,
                    description=group.description,
                    user_id=group.user_id,
                    created_at=group.created_at,
                    updated_at=group.updated_at,
                    device_count=device_count
                )
            )
        
        total_pages = (total + page_size - 1) // page_size
        
        return DeviceGroupListResponse(
            groups=group_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def update_group(
        self, 
        group_id: int, 
        update_data: DeviceGroupUpdate, 
        user_id: int
    ) -> DeviceGroupResponse:
        """Update device group."""
        group = await self.device_group_repo.get_group(group_id)
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device group not found"
            )
        
        # Check ownership
        if group.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_group = await self.device_group_repo.update_group(group_id, update_dict)
        
        device_count = len(updated_group.group_items) if updated_group.group_items else 0
        
        return DeviceGroupResponse(
            id=updated_group.id,
            name=updated_group.name,
            description=updated_group.description,
            user_id=updated_group.user_id,
            created_at=updated_group.created_at,
            updated_at=updated_group.updated_at,
            device_count=device_count
        )
    
    async def delete_group(self, group_id: int, user_id: int) -> bool:
        """Delete device group."""
        group = await self.device_group_repo.get_group(group_id)
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device group not found"
            )
        
        # Check ownership
        if group.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return await self.device_group_repo.delete_group(group_id)
    
    async def add_devices_to_group(
        self, 
        group_id: int, 
        devices_data: DeviceGroupAddDevices, 
        user_id: int
    ) -> DeviceGroupDetailResponse:
        """Add devices to a group."""
        group = await self.device_group_repo.get_group(group_id)
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device group not found"
            )
        
        # Check ownership
        if group.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Add parent devices
        if devices_data.device_ids:
            for device_id in devices_data.device_ids:
                device = await self.device_group_repo.get_device(device_id)
                if device:
                    await self.device_group_repo.add_device_to_group(
                        group_id, device_id=device_id
                    )
        
        # Add child devices
        if devices_data.child_device_ids:
            for child_id in devices_data.child_device_ids:
                child = await self.device_group_repo.get_child_device(child_id)
                if child:
                    await self.device_group_repo.add_device_to_group(
                        group_id, child_device_id=child_id
                    )
        
        # Return updated group
        return await self.get_group(group_id, user_id)
    
    async def remove_devices_from_group(
        self, 
        group_id: int, 
        devices_data: DeviceGroupRemoveDevices, 
        user_id: int
    ) -> DeviceGroupDetailResponse:
        """Remove devices from a group."""
        group = await self.device_group_repo.get_group(group_id)
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device group not found"
            )
        
        # Check ownership
        if group.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Remove parent devices
        if devices_data.device_ids:
            for device_id in devices_data.device_ids:
                await self.device_group_repo.remove_device_from_group(
                    group_id, device_id=device_id
                )
        
        # Remove child devices
        if devices_data.child_device_ids:
            for child_id in devices_data.child_device_ids:
                await self.device_group_repo.remove_device_from_group(
                    group_id, child_device_id=child_id
                )
        
        # Return updated group
        return await self.get_group(group_id, user_id)
    
    async def borrow_group_devices(
        self,
        group_id: int,
        borrow_data: DeviceGroupBorrowRequest,
        user_id: int
    ) -> DeviceGroupBorrowResponse:
        """Borrow all devices in a group (batch operation)."""
        if not self.loan_repo:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Loan service not available"
            )
        
        # Get group
        group = await self.device_group_repo.get_group(group_id)
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device group not found"
            )
        
        # Check ownership
        if group.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check device availability
        availability = await self.device_group_repo.check_group_devices_availability(group_id)
        
        print("=" * 60)
        print(f"🔍 [DeviceGroupService] Group {group_id} availability check:")
        print(f"  all_available: {availability['all_available']}")
        print(f"  total_devices: {availability.get('total_devices', 0)}")
        print(f"  device_details count: {len(availability.get('device_details', []))}")
        for i, dev in enumerate(availability.get('device_details', [])):
            print(f"    Device {i+1}: id={dev.get('id')}, name={dev.get('name')}, is_child={dev.get('is_child')}")
        print("=" * 60)
        
        if not availability["all_available"]:
            unavailable_list = []
            for device in availability["unavailable_devices"]:
                unavailable_list.append({
                    "name": device["name"],
                    "status": device["status"]
                })
            
            return DeviceGroupBorrowResponse(
                success=False,
                message="Tidak semua perangkat dalam grup tersedia",
                unavailable_devices=unavailable_list
            )
        
        # ✅ Build loan items - CRITICAL SECTION
        loan_items = []
        borrowed_device_names = []
        
        print("🔧 [DeviceGroupService] Building loan items:")
        
        # ✅ IMPORTANT: Loop through ALL device_details
        for i, device_info in enumerate(availability["device_details"]):
            print(f"  Processing device {i+1}/{len(availability['device_details'])}:")
            print(f"    id: {device_info.get('id')}")
            print(f"    name: {device_info.get('name')}")
            print(f"    is_child: {device_info.get('is_child')}")
            
            # Create loan item dict
            loan_item_dict = {
                "device_id": None if device_info["is_child"] else device_info["id"],
                "child_device_id": device_info["id"] if device_info["is_child"] else None,
                "quantity": 1,
                "condition_before": "BAIK",
                "condition_notes": None
            }
            
            print(f"    → Created loan_item: device_id={loan_item_dict['device_id']}, child_device_id={loan_item_dict['child_device_id']}")
            
            loan_items.append(loan_item_dict)
            borrowed_device_names.append(device_info["name"])
        
        print(f"✅ [DeviceGroupService] Total loan items created: {len(loan_items)}")
        print(f"   Loan items list: {loan_items}")
        print("=" * 60)
        
        # ✅ VERIFY loan_items is not empty
        if not loan_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No devices to borrow in group"
            )
        
        # Create loan data
        loan_create_dict = {
            "assignment_letter_number": borrow_data.assignment_letter_number,
            "assignment_letter_date": borrow_data.assignment_letter_date,
            "borrower_name": borrow_data.borrower_name,
            "activity_name": borrow_data.activity_name,
            "usage_duration_days": borrow_data.usage_duration_days,
            "loan_start_date": borrow_data.loan_start_date,
            "purpose": borrow_data.purpose,
            "monitoring_devices": borrow_data.monitoring_devices,
            "pihak_1_id": borrow_data.pihak_1_id,
            "pihak_2_id": borrow_data.pihak_2_id,
            "loan_items": loan_items  # ← Should have 3 items
        }
        
        print(f"🚀 [DeviceGroupService] Creating loan with {len(loan_items)} items")
        
        # Convert to Pydantic model
        loan_create_data = DeviceLoanCreate(**loan_create_dict)
        
        print(f"✅ [DeviceGroupService] DeviceLoanCreate validated with {len(loan_create_data.loan_items)} items")
        
        try:
            # Import the service here to avoid circular import
            from src.services.loan import LoanService
            
            # Create loan service instance
            loan_service = LoanService(self.loan_repo, self.device_repo)
            loan_response = await loan_service.create_loan(loan_create_data, user_id)
            
            return DeviceGroupBorrowResponse(
                success=True,
                message=f"Berhasil meminjam {len(borrowed_device_names)} perangkat dari grup '{group.name}'",
                loan_id=loan_response.id,
                borrowed_devices=borrowed_device_names
            )
        
        except Exception as e:
            import traceback
            print("❌ [DeviceGroupService] Error creating loan:")
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gagal membuat peminjaman: {str(e)}"
            )
    
    def _build_device_item_response(
        self, 
        item: Any, 
        device: Any
    ) -> DeviceGroupItemResponse:
        """Build device item response from database models."""
        is_available = device.device_status == DeviceStatus.TERSEDIA
        
        return DeviceGroupItemResponse(
            id=item.id,
            group_id=item.group_id,
            device_id=item.device_id,
            child_device_id=item.child_device_id,
            added_at=item.added_at,
            device_name=device.device_name,
            device_code=device.device_code,
            device_status=device.device_status.value if isinstance(device.device_status, DeviceStatus) else device.device_status,
            device_condition=device.device_condition,
            is_available=is_available
        )