"""
Device Export Endpoints with permission-based authorization.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, Union
from datetime import datetime
import logging
import traceback

from src.core.database import get_db
from src.services.device_export_service import DeviceExportService
from src.auth.permissions import get_current_active_user, require_permission
from src.auth.role_permissions import Permission
from src.models.user import User

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# DEVICE EXPORT - Admin and Manager
# ============================================================================

@router.get("/excel", dependencies=[Depends(require_permission(Permission.EXPORT_DEVICE_USAGE))])
async def export_devices_to_excel(
    year: Optional[int] = Query(None, description="Filter by specific year"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by specific month (1-12)"),
    device_ids: Optional[str] = Query(None, description="Comma-separated device IDs to filter"),
    current_user: Union[User, Dict[str, Any]] = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export device usage statistics to Excel.
    
    **Permission Required:** EXPORT_DEVICE_USAGE
    **Roles:** admin, manager
    
    **Query Parameters:**
    - **year**: Filter by specific year (optional)
    - **month**: Filter by specific month (1-12, requires year) (optional)
    - **device_ids**: Comma-separated device IDs to filter (optional)
    
    **Response:**
    - Excel file (.xlsx) with device usage statistics
    """
    # Handle both User object and dict
    username = current_user.username if hasattr(current_user, 'username') else current_user.get('username', 'Unknown')
    
    logger.info(f"📥 Export request from user: {username}")
    logger.info(f"   Filters - year: {year}, month: {month}, device_ids: {device_ids}")
    
    try:
        # Parse device IDs if provided
        parsed_device_ids = None
        if device_ids:
            try:
                parsed_device_ids = [int(id.strip()) for id in device_ids.split(",")]
                logger.info(f"   Parsed device IDs: {parsed_device_ids}")
            except ValueError as ve:
                logger.error(f"❌ Invalid device_ids format: {ve}")
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid device_ids format. Must be comma-separated integers."
                )
        
        # Validate month requires year
        if month and not year:
            logger.error("❌ Month specified without year")
            raise HTTPException(
                status_code=400, 
                detail="Month filter requires year to be specified"
            )
        
        # Create export service
        logger.info("🔧 Creating export service...")
        export_service = DeviceExportService(db)
        
        # Generate Excel file
        logger.info("📊 Starting Excel generation...")
        try:
            excel_buffer = await export_service.export_device_usage_to_excel(
                year=year,
                month=month,
                device_ids=parsed_device_ids
            )
            logger.info(f"✅ Excel generated successfully: {excel_buffer.getbuffer().nbytes} bytes")
            
        except Exception as e:
            logger.error(f"❌ Error during Excel generation: {str(e)}")
            logger.error(f"   Exception type: {type(e).__name__}")
            logger.error(f"   Traceback:\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate Excel file: {str(e)}"
            )
        
        # Generate filename
        filename_parts = ["device_usage_report"]
        if year:
            filename_parts.append(f"{year}")
        if month:
            filename_parts.append(f"{month:02d}")
        if parsed_device_ids:
            filename_parts.append("filtered")
        filename_parts.append(datetime.now().strftime("%Y%m%d_%H%M%S"))
        filename = "_".join(filename_parts) + ".xlsx"
        
        logger.info(f"📤 Sending file: {filename}")
        
        # Return as downloadable file
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"💥 Unexpected error in export endpoint: {str(e)}")
        logger.error(f"   Exception type: {type(e).__name__}")
        logger.error(f"   Traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# ============================================================================
# ADMIN-ONLY EXPORT - Admin Only
# ============================================================================

@router.get("/excel/admin", dependencies=[Depends(require_permission(Permission.EXPORT_EXCEL))])
async def export_devices_to_excel_admin(
    year: Optional[int] = Query(None, description="Filter by specific year"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by specific month (1-12)"),
    device_ids: Optional[str] = Query(None, description="Comma-separated device IDs to filter"),
    current_user: Union[User, Dict[str, Any]] = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export device usage statistics to Excel (Admin only).
    
    **Permission Required:** EXPORT_EXCEL
    **Roles:** admin only
    
    **Query Parameters:**
    - **year**: Filter by specific year (optional)
    - **month**: Filter by specific month (1-12, requires year) (optional)
    - **device_ids**: Comma-separated device IDs to filter (optional)
    
    **Response:**
    - Excel file (.xlsx) with device usage statistics (admin version with additional data)
    """
    # Handle both User object and dict
    username = current_user.username if hasattr(current_user, 'username') else current_user.get('username', 'Unknown')
    
    logger.info(f"📥 Admin export request from user: {username}")
    
    try:
        # Parse device IDs if provided
        parsed_device_ids = None
        if device_ids:
            try:
                parsed_device_ids = [int(id.strip()) for id in device_ids.split(",")]
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid device_ids format. Must be comma-separated integers."
                )
        
        # Validate month requires year
        if month and not year:
            raise HTTPException(
                status_code=400, 
                detail="Month filter requires year to be specified"
            )
        
        # Create export service
        export_service = DeviceExportService(db)
        
        # Generate Excel file
        try:
            excel_buffer = await export_service.export_device_usage_to_excel(
                year=year,
                month=month,
                device_ids=parsed_device_ids
            )
        except Exception as e:
            logger.error(f"❌ Admin export error: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate Excel file: {str(e)}"
            )
        
        # Generate filename
        filename_parts = ["device_usage_report_admin"]
        if year:
            filename_parts.append(f"{year}")
        if month:
            filename_parts.append(f"{month:02d}")
        if parsed_device_ids:
            filename_parts.append("filtered")
        filename_parts.append(datetime.now().strftime("%Y%m%d_%H%M%S"))
        filename = "_".join(filename_parts) + ".xlsx"
        
        # Return as downloadable file
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Unexpected admin export error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )