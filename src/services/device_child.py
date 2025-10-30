"""Service layer for DeviceChild (child devices management)."""

from typing import Optional
from fastapi import UploadFile, HTTPException, status
from datetime import datetime
import os

from src.repositories.device_child import DeviceChildRepository
from src.repositories.device import DeviceRepository  # untuk validasi parent
from src.schemas.device_child import (
    DeviceChildCreate,
    DeviceChildUpdate,
    DeviceChildResponse,
    DeviceChildListResponse,
)

# Folder upload untuk child devices
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
CHILD_UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads", "device_children")


class DeviceChildService:
    def __init__(self, device_child_repo: DeviceChildRepository, device_repo: DeviceRepository):
        self.device_child_repo = device_child_repo
        self.device_repo = device_repo

    # -----------------------------------------------------------
    # 📌 CREATE
    # -----------------------------------------------------------
    async def create_child(self, data: DeviceChildCreate) -> DeviceChildResponse:
        parent = await self.device_repo.get_by_id(data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent device with ID {data.parent_id} not found"
            )

        # ⚠️ Hapus pengecekan duplikat
        new_child = await self.device_child_repo.create(data)
        return DeviceChildResponse.model_validate(new_child)


    # -----------------------------------------------------------
    # 📌 GET ONE
    # -----------------------------------------------------------
    async def get_child(self, child_id: int) -> Optional[DeviceChildResponse]:
        child = await self.device_child_repo.get_by_id(child_id)
        if not child:
            raise HTTPException(status_code=404, detail="Device child not found")
        return DeviceChildResponse.model_validate(child)

    # -----------------------------------------------------------
    # 📌 GET ALL
    # -----------------------------------------------------------
    async def get_all_children(
        self,
        skip: int = 0,
        limit: int = 10,
        parent_id: Optional[int] = None
    ) -> DeviceChildListResponse:
        children, total = await self.device_child_repo.get_all(skip, limit, parent_id)

        return DeviceChildListResponse(
            children=[DeviceChildResponse.model_validate(child) for child in children],
            total=total,
            page=(skip // limit) + 1,
            page_size=limit,
            total_pages=(total + limit - 1) // limit
        )

    # -----------------------------------------------------------
    # 📌 UPDATE
    # -----------------------------------------------------------
    async def update_child(self, child_id: int, updates: DeviceChildUpdate) -> DeviceChildResponse:
        existing = await self.device_child_repo.get_by_id(child_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Device child not found")
    
        # ⚠️ Hapus pengecekan duplikat juga
        updated = await self.device_child_repo.update(child_id, updates)
        return DeviceChildResponse.model_validate(updated)


    # -----------------------------------------------------------
    # 📌 DELETE
    # -----------------------------------------------------------
    async def delete_child(self, child_id: int) -> bool:
        deleted = await self.device_child_repo.delete(child_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Device child not found")
        return deleted

    # -----------------------------------------------------------
    # 📸 UPLOAD PHOTO
    # -----------------------------------------------------------
    async def upload_child_photo(self, child_id: int, file: UploadFile):
        """Upload foto perangkat anak dan ganti foto lama sepenuhnya."""
        child = await self.device_child_repo.get_by_id(child_id)
        if not child:
            raise HTTPException(status_code=404, detail="Device child not found")

        os.makedirs(CHILD_UPLOAD_DIR, exist_ok=True)

        allowed_exts = [".jpg", ".jpeg", ".png", ".webp"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_exts:
            raise HTTPException(status_code=400, detail="Only JPG, PNG, and WEBP formats are allowed")

        # Hapus foto lama
        if child.photos_url:
            for old_path in child.photos_url:
                abs_old_path = os.path.join(BASE_DIR, old_path.lstrip("/"))
                if os.path.exists(abs_old_path):
                    os.remove(abs_old_path)

        filename = f"{child.device_code}_{int(datetime.utcnow().timestamp())}{file_ext}"
        file_path = os.path.join(CHILD_UPLOAD_DIR, filename)

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        rel_path = f"/static/uploads/device_children/{filename}"
        child.photos_url = [rel_path]

        await self.device_child_repo.update(child_id, DeviceChildUpdate(photos_url=child.photos_url))

        updated_child = await self.device_child_repo.get_by_id(child_id)
        return updated_child

    # -----------------------------------------------------------
    # 🗑️ DELETE PHOTO
    # -----------------------------------------------------------
    async def delete_child_photo(self, child_id: int, filename: str):
        """Hapus satu foto perangkat anak berdasarkan filename."""
        child = await self.device_child_repo.get_by_id(child_id)
        if not child:
            raise HTTPException(status_code=404, detail="Device child not found")

        if not child.photos_url:
            raise HTTPException(status_code=404, detail="No photos to delete")

        new_photos = []
        deleted_path = None
        for path in child.photos_url:
            if filename in path:
                deleted_path = path
            else:
                new_photos.append(path)

        if not deleted_path:
            raise HTTPException(status_code=404, detail="Photo not found")

        abs_path = os.path.join(BASE_DIR, deleted_path.lstrip("/"))
        if os.path.exists(abs_path):
            os.remove(abs_path)

        child.photos_url = new_photos
        await self.device_child_repo.update(child_id, DeviceChildUpdate(photos_url=child.photos_url))

        updated_child = await self.device_child_repo.get_by_id(child_id)
        return updated_child

    # -----------------------------------------------------------
    # 📷 GET PHOTO
    # -----------------------------------------------------------
    async def get_child_photos(self, child_id: int):
        """Ambil semua foto dari perangkat anak tertentu."""
        child = await self.device_child_repo.get_by_id(child_id)
        if not child:
            raise HTTPException(status_code=404, detail="Device child not found")
        return child.photos_url or []
