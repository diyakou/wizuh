from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum, JSON, select, and_, cast
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session, mapped_column, Mapped
from sqlalchemy.sql import func
from sqlalchemy.types import Integer as IntegerType, DateTime as DateTimeType
from sqlalchemy.sql.expression import ColumnElement, BinaryExpression
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.sql.operators import gt, lt, le, eq
from datetime import datetime, timedelta
import enum
import uuid
from cryptography.fernet import Fernet
import json
import os
from typing import List, Optional, Dict, Any, cast as type_cast, TypeVar, Union, Tuple, Type, Generic, Sequence, ClassVar, ForwardRef
from database.db import Base, session

# Initialize encryption key
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', Fernet.generate_key())
fernet = Fernet(ENCRYPTION_KEY)


T = TypeVar('T')

def safe_cast(value: Any, target_type: Type[T]) -> Optional[T]:
    """Safely cast a value to a target type."""
    try:
        return target_type(value) if value is not None else None
    except (ValueError, TypeError):
        return None

class ColumnCast(Generic[T]):
    """Helper class for casting SQLAlchemy columns."""
    @staticmethod
    def to_type(column: ColumnElement[Any], target_type: Type[TypeEngine[T]]) -> ColumnElement[T]:
        """Cast a SQLAlchemy column to a target type."""
        return cast(column, target_type)

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    RESELLER = "reseller"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone = Column(String(20))
    balance = Column(Float, default=0.0)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    configs = relationship("XUIConfig", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

    @classmethod
    def get_by_telegram_id(cls, telegram_id: int):
        return session.query(cls).filter_by(telegram_id=telegram_id).first()
    
    @classmethod
    def count_new_users(cls, since: datetime):
        return session.query(cls).filter(cls.created_at >= since).count()

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN


class Server(Base):
    __tablename__ = 'servers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    ip = Column(String(255))
    port = Column(Integer)
    username = Column(String(255))
    password = Column(String(255))
    type = Column(String(50))  # xui, sanaei, etc.
    is_active = Column(Boolean, default=True)
    max_users = Column(Integer)
    current_users = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_check = Column(DateTime)
    
    configs = relationship("Config", back_populates="server")
    
    @classmethod
    def get_all(cls):
        return session.query(cls).all()
    
    @classmethod
    def get_active(cls):
        return session.query(cls).filter_by(is_active=True).all()

class Plan(Base):
    __tablename__ = 'plans'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    volume = Column(Float)  # GB
    duration = Column(Integer)  # days
    price = Column(Float)
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    max_concurrent_users = Column(Integer, default=1)
    protocols = Column(String(255))  # comma-separated list
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @classmethod
    def get_active_plans(cls):
        return session.query(cls).filter_by(is_active=True).all()
    
    @classmethod
    def get_by_id(cls, plan_id: int):
        return session.query(cls).get(plan_id)

class Config(Base):
    __tablename__ = 'configs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    server_id = Column(Integer, ForeignKey('servers.id'))
    name = Column(String(255))
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()))
    protocol = Column(String(50))  # vless, vmess, trojan
    port = Column(Integer)
    volume = Column(Float)  # GB
    used_volume = Column(Float, default=0)
    expiry_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    
    server = relationship("Server", back_populates="configs")
    
    @property
    def remaining_volume(self):
        return max(0, self.volume - self.used_volume)
    
    @property
    def remaining_days(self):
        if not self.expiry_date:
            return 0
        delta = self.expiry_date - datetime.utcnow()
        return max(0, delta.days)
    
    @classmethod
    def get_user_configs(cls, telegram_id: int):
        return (session.query(cls)
                .join(User)
                .filter(User.telegram_id == telegram_id)
                .all())
    
    @classmethod
    def count_active(cls):
        return session.query(cls).filter_by(is_active=True).count()

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    gateway = Column(String(50))  # zarinpal, nextpay, crypto, wallet
    transaction_id = Column(String(255))
    status = Column(String(50))  # pending, completed, failed
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    user = relationship("User", back_populates="transactions")
    
    @classmethod
    def get_daily_income(cls, date: datetime):
        return (session.query(cls)
                .filter(cls.status == "completed")
                .filter(cls.created_at >= date)
                .filter(cls.created_at < date + timedelta(days=1))
                .with_entities(func.sum(cls.amount))
                .scalar() or 0)

class BotSetting(Base):
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(191), unique=True)    
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_value(cls, key: str, default=None):
        setting = session.query(cls).filter_by(key=key).first()
        return setting.value if setting else default
    
    @classmethod
    def set_value(cls, key: str, value: str, description: str = None):
        setting = session.query(cls).filter_by(key=key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = cls(key=key, value=value, description=description)
            session.add(setting)
        session.commit()

class Backup(Base):
    __tablename__ = 'backups'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255))
    size = Column(Integer)  # bytes
    checksum = Column(String(64))  # SHA-256
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50))  # completed, failed
    error_message = Column(Text)
    
    @classmethod
    def create_backup(cls, filename: str, size: int, checksum: str):
        backup = cls(filename=filename, size=size, checksum=checksum, status="completed")
        session.add(backup)
        session.commit()
        return backup

class ServerCategory(Base):
    __tablename__ = 'server_categories'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), unique=True)
    remark = Column(Text, nullable=True)
    flag = Column(String(10), nullable=True)  # For emoji
    server_ids = Column(JSON)  # List of server IDs
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_active_categories(cls):
        return session.query(cls).filter_by(is_active=True).all()
    
    @classmethod
    def get_by_id(cls, category_id: int):
        return session.query(cls).get(category_id)
    
    def get_servers(self):
        """Get all servers in this category."""
        return session.query(Server).filter(Server.id.in_(self.server_ids)).all()
    
    def save(self):
        """Save or update the category."""
        session.add(self)
        session.commit()
        return self

class ServerPlan(Base):
    __tablename__ = 'server_plans'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(191), unique=True)  # Reduced from 255 to 191 to stay within MySQL's key length limit
    volume = Column(Integer)  # Volume in MB
    duration = Column(Integer)  # Duration in days
    price = Column(Integer)  # Price in Toman
    category_id = Column(Integer, ForeignKey('server_categories.id'), nullable=True)
    server_ids = Column(JSON)  # List of server IDs
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("ServerCategory", foreign_keys=[category_id])
    configs = relationship("XUIConfig", back_populates="plan")
    
    @classmethod
    def get_active_plans(cls):
        return session.query(cls).filter_by(is_active=True).all()
    
    @classmethod
    def get_by_id(cls, plan_id: int):
        return session.query(cls).get(plan_id)
    
    def get_servers(self):
        """Get all servers in this plan."""
        return session.query(Server).filter(Server.id.in_(self.server_ids)).all()
    
    def save(self):
        """Save or update the plan."""
        session.add(self)
        session.commit()
        return self

class SettingType(enum.Enum):
    PAYMENT_GATEWAY = "payment_gateway"
    CHANNEL = "channel"
    SYSTEM = "system"

class Setting(Base):
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(191), unique=True)
    value = Column(Text)  # Encrypted for sensitive data
    type = Column(String(50))  # Using SettingType enum values
    status = Column(Boolean, default=True)
    extra = Column(JSON, nullable=True)  # For additional settings like bank name, discount, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def decrypted_value(self):
        """Get decrypted value for sensitive data."""
        if self.type == SettingType.PAYMENT_GATEWAY.value:
            try:
                return fernet.decrypt(self.value.encode()).decode()
            except:
                return self.value
        return self.value
    
    @classmethod
    def get_payment_gateways(cls):
        """Get all payment gateway settings."""
        return session.query(cls).filter_by(
            type=SettingType.PAYMENT_GATEWAY.value,
            status=True
        ).all()
    
    @classmethod
    def get_channels(cls):
        """Get all channel settings."""
        return session.query(cls).filter_by(
            type=SettingType.CHANNEL.value,
            status=True
        ).all()
    
    @classmethod
    def get_by_key(cls, key: str):
        """Get setting by key."""
        return session.query(cls).filter_by(key=key).first()
    
    def save(self):
        """Save or update the setting."""
        
        # Encrypt sensitive data
        if self.type == SettingType.PAYMENT_GATEWAY.value:
            try:
                self.value = fernet.encrypt(self.value.encode()).decode()
            except:
                pass
        
        session.add(self)
        session.commit()
        return self
    
    @classmethod
    def create_payment_gateway(cls, name: str, gateway_type: str, api_key: str, extra: dict = None):
        """Create a new payment gateway setting."""
        key = f"{gateway_type}_{name.lower().replace(' ', '_')}"
        setting = cls(
            key=key,
            value=api_key,
            type=SettingType.PAYMENT_GATEWAY.value,
            status=True,
            extra=extra or {}
        )
        return setting.save()
    
    @classmethod
    def create_channel(cls, name: str, channel_id: str, channel_type: str, is_mandatory: bool = False):
        """Create a new channel setting."""
        key = f"channel_{name.lower().replace(' ', '_')}"
        setting = cls(
            key=key,
            value=channel_id,
            type=SettingType.CHANNEL.value,
            status=True,
            extra={
                'type': channel_type,
                'mandatory': is_mandatory
            }
        )
        return setting.save()
    
    def to_dict(self):
        """Convert setting to dictionary."""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.decrypted_value if self.type == SettingType.PAYMENT_GATEWAY.value else self.value,
            'type': self.type,
            'status': self.status,
            'extra': self.extra
        }

class ServerProtocol(enum.Enum):
    """Supported V2Ray protocols."""
    VMESS = "vmess"
    VLESS = "vless"
    TROJAN = "trojan"

class XUIServer(Base):
    """Model for X-UI server information."""
    __tablename__ = 'xui_servers'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(100))
    password: Mapped[Optional[str]] = mapped_column(String(100))
    token: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())
    
    configs: Mapped[List["XUIConfig"]] = relationship("XUIConfig", back_populates="server")
    
    @classmethod
    def get_active_servers(cls) -> Sequence["XUIServer"]:
        """Get all active X-UI servers."""
        stmt = select(cls).where(cls.status.is_(True))
        result = session.execute(stmt)
        return result.scalars().all()

class XUIConfig(Base):
    """Model for X-UI config information."""
    __tablename__ = 'xui_configs'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    server_id: Mapped[int] = mapped_column(Integer, ForeignKey('xui_servers.id'), nullable=False)
    protocol: Mapped[ServerProtocol] = mapped_column(Enum(ServerProtocol), nullable=False)
    uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    inbound_id: Mapped[int] = mapped_column(Integer, nullable=False)
    total_gb: Mapped[int] = mapped_column(Integer, nullable=False)  # Total GB allowed
    used_gb: Mapped[int] = mapped_column(Integer, default=0)  # GB used so far
    expiry_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey('server_plans.id'))
    plan: Mapped["ServerPlan"] = relationship("ServerPlan", back_populates="configs")
    user: Mapped[ForwardRef("User")] = relationship("User", back_populates="configs") # type: ignore
    server: Mapped[XUIServer] = relationship("XUIServer", back_populates="configs")
    
    @classmethod
    def get_active_configs(cls) -> Sequence["XUIConfig"]:
        """Get all active configs (not expired and with remaining traffic)."""
        now = datetime.now()
        stmt = select(cls).where(and_(
            gt(cls.expiry_time, now),
            lt(cls.used_gb, cls.total_gb)
        ))
        result = session.execute(stmt)
        return result.scalars().all()
    
    @classmethod
    def get_expired_configs(cls) -> Sequence["XUIConfig"]:
        """Get all expired configs."""
        now = datetime.now()
        stmt = select(cls).where(le(cls.expiry_time, now))
        result = session.execute(stmt)
        return result.scalars().all()
    
    @classmethod
    def get_user_configs(cls, user_id: int) -> Sequence["XUIConfig"]:
        """Get all configs for a specific user."""
        stmt = select(cls).where(eq(cls.user_id, user_id))
        result = session.execute(stmt)
        return result.scalars().all()
    
    def get_remaining_gb(self) -> int:
        """Get remaining GB for this config."""
        stmt = select(
            ColumnCast[int].to_type(self.used_gb, IntegerType),
            ColumnCast[int].to_type(self.total_gb, IntegerType)
        )
        result = session.execute(stmt).first()
        if not result:
            return 0
        used, total = result
        used_gb = safe_cast(used, int) or 0
        total_gb = safe_cast(total, int) or 0
        return max(0, total_gb - used_gb)
    
    def get_remaining_days(self) -> int:
        """Get remaining days for this config."""
        stmt = select(ColumnCast[datetime].to_type(self.expiry_time, DateTimeType))
        result = session.execute(stmt).scalar()
        expiry = safe_cast(result, datetime)
        if not expiry:
            return 0
        now = datetime.now()
        if expiry <= now:
            return 0
        return (expiry - now).days
    
    def is_active(self) -> bool:
        """Check if config is active (not expired and has remaining traffic)."""
        stmt = select(
            ColumnCast[datetime].to_type(self.expiry_time, DateTimeType),
            ColumnCast[int].to_type(self.used_gb, IntegerType),
            ColumnCast[int].to_type(self.total_gb, IntegerType)
        )
        result = session.execute(stmt).first()
        if not result:
            return False
        expiry, used, total = result
        expiry_time = safe_cast(expiry, datetime)
        used_gb = safe_cast(used, int)
        total_gb = safe_cast(total, int)
        if not all([expiry_time, used_gb is not None, total_gb is not None]):
            return False
        return expiry_time > datetime.now() and used_gb < total_gb

# Update User model to include configs relationship
User.configs = relationship("XUIConfig", back_populates="user")

# Update ServerPlan model to include configs relationship
ServerPlan.configs = relationship("XUIConfig", back_populates="plan") 