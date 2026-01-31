"""
Alarm API endpoints.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List
from models.schemas import (
    AlarmCreateRequest,
    Alarm,
    AlarmConfig
)
from engines.alarm_system import AlarmSystem
from utils.database import get_db
from utils.logger import setup_logger
from sqlalchemy.orm import Session
import uuid

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/alarms", tags=["alarms"])


def get_alarm_system(db: Session = Depends(get_db)) -> AlarmSystem:
    """Dependency to get alarm system instance."""
    return AlarmSystem(db)


@router.post("", response_model=Alarm, status_code=201)
async def create_alarm(
    request: AlarmCreateRequest,
    http_request: Request,
    alarm_system: AlarmSystem = Depends(get_alarm_system)
):
    """
    Create a new alarm.
    
    - **config**: Alarm configuration including:
        - coin: Coin symbol
        - type: Alarm type (price, signal, success_probability)
        - condition: Condition operator (above, below, equals)
        - threshold: Threshold value
        - notification_channels: List of channels (email, web_push)
        - auto_disable: Auto-disable after trigger
        - active: Initial active state
    
    Returns the created alarm with ID.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    # TODO: Get user_id from authentication
    user_id = "default_user"  # Placeholder
    
    logger.info(
        f"Creating alarm for {request.config.coin}",
        extra={
            "request_id": request_id,
            "coin": request.config.coin,
            "type": request.config.type,
            "condition": request.config.condition,
            "threshold": request.config.threshold
        }
    )
    
    try:
        alarm_id = alarm_system.create_alarm(user_id, request.config)
        alarm = alarm_system.get_alarm(alarm_id)
        
        logger.info(
            f"Successfully created alarm with ID: {alarm_id}",
            extra={"request_id": request_id, "alarm_id": alarm_id}
        )
        
        return alarm
        
    except Exception as e:
        logger.error(
            f"Error creating alarm: {str(e)}",
            extra={"request_id": request_id, "coin": request.config.coin},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create alarm: {str(e)}"
        )


@router.get("", response_model=List[Alarm])
async def list_alarms(
    active_only: bool = False,
    http_request: Request = None,
    alarm_system: AlarmSystem = Depends(get_alarm_system)
):
    """
    List all alarms.
    
    - **active_only**: If true, only return active alarms (default: false)
    
    Returns list of all alarms.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4())) if http_request else None
    
    # TODO: Get user_id from authentication
    user_id = "default_user"  # Placeholder
    
    logger.info(
        f"Listing alarms (active_only={active_only})",
        extra={"request_id": request_id, "active_only": active_only}
    )
    
    try:
        alarms = alarm_system.list_alarms(user_id, active_only)
        return alarms
        
    except Exception as e:
        logger.error(
            f"Error listing alarms: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list alarms: {str(e)}"
        )


@router.put("/{alarm_id}", response_model=Alarm)
async def update_alarm(
    alarm_id: str,
    updates: dict,
    http_request: Request,
    alarm_system: AlarmSystem = Depends(get_alarm_system)
):
    """
    Update an existing alarm.
    
    - **alarm_id**: ID of the alarm to update
    - **updates**: Dictionary of fields to update (e.g., {"active": false, "threshold": 50000})
    
    Returns the updated alarm.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    logger.info(
        f"Updating alarm {alarm_id}",
        extra={"request_id": request_id, "alarm_id": alarm_id, "updates": updates}
    )
    
    try:
        alarm_system.update_alarm(alarm_id, updates)
        alarm = alarm_system.get_alarm(alarm_id)
        
        if not alarm:
            raise HTTPException(
                status_code=404,
                detail=f"Alarm with ID {alarm_id} not found"
            )
        
        logger.info(
            f"Successfully updated alarm {alarm_id}",
            extra={"request_id": request_id, "alarm_id": alarm_id}
        )
        
        return alarm
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating alarm: {str(e)}",
            extra={"request_id": request_id, "alarm_id": alarm_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update alarm: {str(e)}"
        )


@router.delete("/{alarm_id}", response_model=dict)
async def delete_alarm(
    alarm_id: str,
    http_request: Request,
    alarm_system: AlarmSystem = Depends(get_alarm_system)
):
    """
    Delete an alarm.
    
    - **alarm_id**: ID of the alarm to delete
    
    Returns confirmation message.
    """
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    
    logger.info(
        f"Deleting alarm {alarm_id}",
        extra={"request_id": request_id, "alarm_id": alarm_id}
    )
    
    try:
        alarm_system.delete_alarm(alarm_id)
        
        logger.info(
            f"Successfully deleted alarm {alarm_id}",
            extra={"request_id": request_id, "alarm_id": alarm_id}
        )
        
        return {
            "message": f"Successfully deleted alarm",
            "alarm_id": alarm_id
        }
        
    except Exception as e:
        logger.error(
            f"Error deleting alarm: {str(e)}",
            extra={"request_id": request_id, "alarm_id": alarm_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete alarm: {str(e)}"
        )
