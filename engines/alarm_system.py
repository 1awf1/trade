"""
Alarm System Engine
Manages alarm CRUD operations, checking, and notifications.
"""
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.database import Alarm as AlarmDB, AlarmHistory as AlarmHistoryDB, User
from models.schemas import (
    Alarm, AlarmConfig, AlarmHistoryRecord, TriggeredAlarm,
    AlarmType, AlarmCondition
)
from utils.logger import setup_logger
from utils.notification import NotificationService

logger = setup_logger(__name__)


class AlarmSystem:
    """
    Alarm System for managing price/signal/probability-based notifications.
    
    Responsibilities:
    - Create, update, delete, and list alarms
    - Check alarm conditions
    - Send notifications
    - Track alarm history
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize alarm system.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def create_alarm(self, user_id: str, config: AlarmConfig) -> str:
        """
        Create a new alarm.
        
        Args:
            user_id: User ID
            config: Alarm configuration
            
        Returns:
            Alarm ID
            
        Validates: Requirement 18.1, 18.2, 18.3
        """
        try:
            # Validate notification channels
            valid_channels = ["email", "web_push"]
            for channel in config.notification_channels:
                if channel not in valid_channels:
                    raise ValueError(f"Invalid notification channel: {channel}")
            
            # Create alarm in database
            alarm_db = AlarmDB(
                user_id=user_id,
                coin=config.coin.upper(),
                type=config.type.value,
                condition=config.condition.value,
                threshold=Decimal(str(config.threshold)),
                notification_channels=config.notification_channels,
                auto_disable=config.auto_disable,
                active=config.active
            )
            
            self.db.add(alarm_db)
            self.db.commit()
            self.db.refresh(alarm_db)
            
            logger.info(f"Created alarm {alarm_db.id} for user {user_id}, coin {config.coin}")
            return alarm_db.id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create alarm: {e}")
            raise
    
    def update_alarm(self, alarm_id: str, updates: Dict) -> None:
        """
        Update an existing alarm.
        
        Args:
            alarm_id: Alarm ID
            updates: Dictionary of fields to update
            
        Validates: Requirement 18.1
        """
        try:
            alarm_db = self.db.query(AlarmDB).filter(AlarmDB.id == alarm_id).first()
            
            if not alarm_db:
                raise ValueError(f"Alarm {alarm_id} not found")
            
            # Update allowed fields
            allowed_fields = [
                'threshold', 'notification_channels', 'auto_disable', 'active'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == 'threshold':
                        value = Decimal(str(value))
                    setattr(alarm_db, field, value)
            
            self.db.commit()
            logger.info(f"Updated alarm {alarm_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update alarm {alarm_id}: {e}")
            raise
    
    def delete_alarm(self, alarm_id: str) -> None:
        """
        Delete an alarm.
        
        Args:
            alarm_id: Alarm ID
            
        Validates: Requirement 18.1
        """
        try:
            alarm_db = self.db.query(AlarmDB).filter(AlarmDB.id == alarm_id).first()
            
            if not alarm_db:
                raise ValueError(f"Alarm {alarm_id} not found")
            
            self.db.delete(alarm_db)
            self.db.commit()
            
            logger.info(f"Deleted alarm {alarm_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete alarm {alarm_id}: {e}")
            raise
    
    def list_alarms(self, user_id: str, active_only: bool = False) -> List[Alarm]:
        """
        List all alarms for a user.
        
        Args:
            user_id: User ID
            active_only: If True, only return active alarms
            
        Returns:
            List of alarms
            
        Validates: Requirement 18.1
        """
        try:
            query = self.db.query(AlarmDB).filter(AlarmDB.user_id == user_id)
            
            if active_only:
                query = query.filter(AlarmDB.active == True)
            
            alarms_db = query.order_by(AlarmDB.created_at.desc()).all()
            
            # Convert to Pydantic models
            alarms = []
            for alarm_db in alarms_db:
                config = AlarmConfig(
                    coin=alarm_db.coin,
                    type=AlarmType(alarm_db.type),
                    condition=AlarmCondition(alarm_db.condition),
                    threshold=float(alarm_db.threshold),
                    notification_channels=alarm_db.notification_channels,
                    auto_disable=alarm_db.auto_disable,
                    active=alarm_db.active
                )
                
                alarm = Alarm(
                    id=alarm_db.id,
                    config=config,
                    created_at=alarm_db.created_at,
                    last_triggered=alarm_db.last_triggered,
                    trigger_count=alarm_db.trigger_count
                )
                alarms.append(alarm)
            
            return alarms
            
        except Exception as e:
            logger.error(f"Failed to list alarms for user {user_id}: {e}")
            raise
    
    def get_alarm(self, alarm_id: str) -> Optional[Alarm]:
        """
        Get a specific alarm by ID.
        
        Args:
            alarm_id: Alarm ID
            
        Returns:
            Alarm or None if not found
        """
        try:
            alarm_db = self.db.query(AlarmDB).filter(AlarmDB.id == alarm_id).first()
            
            if not alarm_db:
                return None
            
            config = AlarmConfig(
                coin=alarm_db.coin,
                type=AlarmType(alarm_db.type),
                condition=AlarmCondition(alarm_db.condition),
                threshold=float(alarm_db.threshold),
                notification_channels=alarm_db.notification_channels,
                auto_disable=alarm_db.auto_disable,
                active=alarm_db.active
            )
            
            alarm = Alarm(
                id=alarm_db.id,
                config=config,
                created_at=alarm_db.created_at,
                last_triggered=alarm_db.last_triggered,
                trigger_count=alarm_db.trigger_count
            )
            
            return alarm
            
        except Exception as e:
            logger.error(f"Failed to get alarm {alarm_id}: {e}")
            raise
    
    def check_alarms(self, current_data: Dict[str, Dict]) -> List[TriggeredAlarm]:
        """
        Check all active alarms against current data.
        
        Args:
            current_data: Dictionary mapping coin -> {price, signal, success_probability}
            
        Returns:
            List of triggered alarms
            
        Validates: Requirement 18.4
        """
        try:
            triggered = []
            
            # Get all active alarms
            alarms_db = self.db.query(AlarmDB).filter(AlarmDB.active == True).all()
            
            for alarm_db in alarms_db:
                coin = alarm_db.coin
                
                # Skip if no data for this coin
                if coin not in current_data:
                    continue
                
                data = current_data[coin]
                
                # Get the value to check based on alarm type
                if alarm_db.type == AlarmType.PRICE.value:
                    current_value = data.get('price')
                elif alarm_db.type == AlarmType.SIGNAL.value:
                    current_value = data.get('signal')
                elif alarm_db.type == AlarmType.SUCCESS_PROBABILITY.value:
                    current_value = data.get('success_probability')
                else:
                    continue
                
                if current_value is None:
                    continue
                
                # Check condition
                threshold = float(alarm_db.threshold)
                is_triggered = False
                
                if alarm_db.condition == AlarmCondition.ABOVE.value:
                    is_triggered = current_value > threshold
                elif alarm_db.condition == AlarmCondition.BELOW.value:
                    is_triggered = current_value < threshold
                elif alarm_db.condition == AlarmCondition.EQUALS.value:
                    # For equals, use a small tolerance
                    is_triggered = abs(current_value - threshold) < 0.01
                
                if is_triggered:
                    # Convert to Pydantic model
                    config = AlarmConfig(
                        coin=alarm_db.coin,
                        type=AlarmType(alarm_db.type),
                        condition=AlarmCondition(alarm_db.condition),
                        threshold=float(alarm_db.threshold),
                        notification_channels=alarm_db.notification_channels,
                        auto_disable=alarm_db.auto_disable,
                        active=alarm_db.active
                    )
                    
                    alarm = Alarm(
                        id=alarm_db.id,
                        config=config,
                        created_at=alarm_db.created_at,
                        last_triggered=alarm_db.last_triggered,
                        trigger_count=alarm_db.trigger_count
                    )
                    
                    triggered_alarm = TriggeredAlarm(
                        alarm=alarm,
                        trigger_data={
                            'coin': coin,
                            'current_value': current_value,
                            'threshold': threshold,
                            'type': alarm_db.type,
                            'condition': alarm_db.condition
                        }
                    )
                    
                    triggered.append(triggered_alarm)
                    
                    # Update alarm in database
                    alarm_db.last_triggered = datetime.utcnow()
                    alarm_db.trigger_count += 1
                    
                    # Auto-disable if configured
                    if alarm_db.auto_disable:
                        alarm_db.active = False
                        logger.info(f"Auto-disabled alarm {alarm_db.id}")
                    
                    # Record in history
                    history = AlarmHistoryDB(
                        alarm_id=alarm_db.id,
                        trigger_value=Decimal(str(current_value)),
                        notification_sent=False  # Will be updated after sending
                    )
                    self.db.add(history)
                    
                    logger.info(f"Alarm {alarm_db.id} triggered for {coin}")
            
            self.db.commit()
            return triggered
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to check alarms: {e}")
            raise
    
    def send_notification(self, alarm: Alarm, trigger_data: Dict, user_email: str = None) -> bool:
        """
        Send notification for triggered alarm.
        
        Args:
            alarm: Triggered alarm
            trigger_data: Data that triggered the alarm
            user_email: User's email address (optional, will be fetched if not provided)
            
        Returns:
            True if notification sent successfully
            
        Validates: Requirement 18.5, 18.6
        """
        try:
            success = True
            
            # Get user email if not provided
            if not user_email:
                alarm_db = self.db.query(AlarmDB).filter(AlarmDB.id == alarm.id).first()
                if alarm_db:
                    user = self.db.query(User).filter(User.id == alarm_db.user_id).first()
                    if user:
                        user_email = user.email
            
            for channel in alarm.config.notification_channels:
                if channel == "email":
                    if user_email:
                        success = success and NotificationService.send_alarm_email(
                            user_email, trigger_data
                        )
                    else:
                        logger.warning(f"No email address for alarm {alarm.id}")
                        success = False
                elif channel == "web_push":
                    # TODO: Get user's web push subscription from database
                    subscription = {}  # Placeholder
                    success = success and NotificationService.send_alarm_web_push(
                        subscription, trigger_data
                    )
            
            # Update notification status in history
            if success:
                # Find the most recent history record for this alarm
                history = self.db.query(AlarmHistoryDB).filter(
                    AlarmHistoryDB.alarm_id == alarm.id
                ).order_by(AlarmHistoryDB.triggered_at.desc()).first()
                
                if history:
                    history.notification_sent = True
                    self.db.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send notification for alarm {alarm.id}: {e}")
            return False
    
    def get_alarm_history(self, alarm_id: str, limit: int = 100) -> List[AlarmHistoryRecord]:
        """
        Get alarm trigger history.
        
        Args:
            alarm_id: Alarm ID
            limit: Maximum number of records to return
            
        Returns:
            List of alarm history records
            
        Validates: Requirement 18.10
        """
        try:
            history_db = self.db.query(AlarmHistoryDB).filter(
                AlarmHistoryDB.alarm_id == alarm_id
            ).order_by(AlarmHistoryDB.triggered_at.desc()).limit(limit).all()
            
            history = []
            for record in history_db:
                history.append(AlarmHistoryRecord(
                    alarm_id=record.alarm_id,
                    triggered_at=record.triggered_at,
                    trigger_value=float(record.trigger_value),
                    notification_sent=record.notification_sent
                ))
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get alarm history for {alarm_id}: {e}")
            raise
    
    def get_user_alarm_history(self, user_id: str, limit: int = 100) -> List[AlarmHistoryRecord]:
        """
        Get all alarm history for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of records to return
            
        Returns:
            List of alarm history records
            
        Validates: Requirement 18.10
        """
        try:
            history_db = self.db.query(AlarmHistoryDB).join(
                AlarmDB, AlarmHistoryDB.alarm_id == AlarmDB.id
            ).filter(
                AlarmDB.user_id == user_id
            ).order_by(AlarmHistoryDB.triggered_at.desc()).limit(limit).all()
            
            history = []
            for record in history_db:
                history.append(AlarmHistoryRecord(
                    alarm_id=record.alarm_id,
                    triggered_at=record.triggered_at,
                    trigger_value=float(record.trigger_value),
                    notification_sent=record.notification_sent
                ))
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get alarm history for user {user_id}: {e}")
            raise



# ============================================================================
# Celery Tasks for Periodic Alarm Checking
# ============================================================================

from utils.celery_app import celery_app
from utils.database import get_db
from engines.data_collector import DataCollector


@celery_app.task(name="check_all_alarms")
def check_all_alarms_task():
    """
    Celery task to check all active alarms periodically.
    This task is scheduled to run every minute via Celery Beat.
    
    Validates: Requirement 18.4, 18.8
    """
    try:
        logger.info("Starting periodic alarm check")
        
        # Get database session
        db = next(get_db())
        
        try:
            # Initialize alarm system
            alarm_system = AlarmSystem(db)
            
            # Get all active alarms to determine which coins we need data for
            alarms_db = db.query(AlarmDB).filter(AlarmDB.active == True).all()
            
            if not alarms_db:
                logger.info("No active alarms to check")
                return
            
            # Collect unique coins
            coins = set(alarm.coin for alarm in alarms_db)
            
            # Collect current data for all coins
            current_data = {}
            data_collector = DataCollector()
            
            for coin in coins:
                try:
                    # Get current price
                    price_data = data_collector.fetch_price_data(coin, "1h")
                    if price_data and len(price_data) > 0:
                        current_price = float(price_data.iloc[-1]['close'])
                        current_data[coin] = {
                            'price': current_price,
                            'signal': None,  # Would need to run analysis
                            'success_probability': None  # Would need to run analysis
                        }
                except Exception as e:
                    logger.error(f"Failed to get data for {coin}: {e}")
                    continue
            
            # Check alarms
            triggered_alarms = alarm_system.check_alarms(current_data)
            
            # Send notifications for triggered alarms
            for triggered_alarm in triggered_alarms:
                try:
                    alarm_system.send_notification(
                        triggered_alarm.alarm,
                        triggered_alarm.trigger_data
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification for alarm {triggered_alarm.alarm.id}: {e}")
            
            logger.info(f"Alarm check completed. {len(triggered_alarms)} alarms triggered.")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to check alarms: {e}")
        raise


# Celery Beat schedule configuration
# Add this to your Celery configuration to enable periodic alarm checking
CELERY_BEAT_SCHEDULE = {
    'check-alarms-every-minute': {
        'task': 'check_all_alarms',
        'schedule': 60.0,  # Run every 60 seconds
    },
}
