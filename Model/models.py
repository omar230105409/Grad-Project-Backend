from datetime import date, datetime, time, timezone, timedelta
from typing import List, Optional
import uuid

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

tz_utc_2 = timezone(timedelta(hours=2)) # placeholder code until i figure out how do you do Timezones properly.

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, nullable= False)
    password_hash: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    timezone: str = Field(default="UTC+2", nullable=False)
    fcm_token: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now(tz_utc_2))

    # table relations
    devices: List["Device"] = Relationship(back_populates="owner")
    medicines: List["Medicine"] = Relationship(back_populates="user", cascade_delete=True)
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user", cascade_delete=True)
    settings: Optional["UserSettings"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False})
    notifications: List["Notification"] = Relationship(back_populates="user", cascade_delete=True)


class UserSettings(SQLModel, table=True):
    __tablename__ = "user_settings"

    user_id: uuid.UUID = Field(primary_key=True, foreign_key="users.id", nullable=False, ondelete="CASCADE")
    snooze_min: int = Field(default=10, nullable=False)
    missed_after_min: int = Field(default=60, nullable=False)
    low_supply_pills: int = Field(default=5, nullable=False)
    buzzer: bool = Field(default=True, nullable=False)
    led_color: str = Field(default="blue", nullable=False)
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None

    user: User = Relationship(back_populates="settings")


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, ondelete="CASCADE")
    token_hash: str = Field(unique=True, nullable=False)
    expires_at: datetime = Field(nullable=False)
    revoked_at: Optional[datetime] = None

    user: User = Relationship(back_populates="refresh_tokens")



class Device(SQLModel, table=True):
    __tablename__ = "devices"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    serial_number: str = Field(unique=True, nullable=False)
    owner_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id", ondelete="SET NULL")
    name: str = Field(default="My bottle", nullable=False)
    firmware_version: str = Field(default="1.0", nullable=False)
    last_seen_at: Optional[datetime] = None
    device_secret_hash: str = Field(nullable=False)
    schedule_version: int = Field(default=0, nullable=False)
    acked_version: int = Field(default=0, nullable=False)
    pairing_code_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Table relations for Device
    owner: Optional[User] = Relationship(back_populates="devices")
    slots: List["Slot"] = Relationship(back_populates="device", cascade_delete=True)
    events: List["DeviceEvent"] = Relationship(back_populates="device", cascade_delete=True)


class DeviceEvent(SQLModel, table=True):
    __tablename__ = "device_events"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    device_id: uuid.UUID = Field(foreign_key="devices.id", nullable=False, ondelete="CASCADE")
    slot_number: Optional[int] = None
    type: str = Field(nullable=False)  # slot_opened, slot_closed, reminder_started, reminder_ignored, sensor_error
    occurred_at: datetime = Field(nullable=False)
    schedule_version: Optional[int] = None
    matched_dose_id: Optional[uuid.UUID] = Field(default=None, foreign_key="dose_logs.id", ondelete="SET NULL")

    # table relations for device event
    device: Device = Relationship(back_populates="events")
    matched_dose: Optional["DoseLog"] = Relationship(back_populates="device_events")




class MedicineCatalog(SQLModel, table=True):
    __tablename__ = "medicine_catalog"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, index=True)
    generic_name: Optional[str] = Field(default=None, index=True)
    strength: Optional[str] = None
    form: Optional[str] = None
    uses: Optional[str] = None
    warnings: Optional[str] = None

    medicines: List["Medicine"] = Relationship(back_populates="catalog")


class Medicine(SQLModel, table=True):
    __tablename__ = "medicines"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, ondelete="CASCADE")
    catalog_id: Optional[int] = Field(default=None, foreign_key="medicine_catalog.id", ondelete="SET NULL")
    name: str = Field(nullable=False)
    dose_amount: str = Field(nullable=False)
    pills_per_dose: int = Field(default=1, nullable=False)
    notes: Optional[str] = None

    # Relationships
    user: User = Relationship(back_populates="medicines")
    catalog: Optional[MedicineCatalog] = Relationship(back_populates="medicines")
    slots: List["Slot"] = Relationship(back_populates="medicine")
    schedules: List["Schedule"] = Relationship(back_populates="medicine", cascade_delete=True)



class Slot(SQLModel, table=True):
    __tablename__ = "slots"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    device_id: uuid.UUID = Field(foreign_key="devices.id", nullable=False, ondelete="CASCADE")
    slot_number: int = Field(nullable=False)
    medicine_id: Optional[uuid.UUID] = Field(default=None, foreign_key="medicines.id", ondelete="SET NULL")
    pills_remaining: int = Field(default=0, nullable=False)

    # Relationships
    device: Device = Relationship(back_populates="slots")
    medicine: Optional[Medicine] = Relationship(back_populates="slots")
    schedules: List["Schedule"] = Relationship(back_populates="slot", cascade_delete=True)


class Schedule(SQLModel, table=True):
    __tablename__ = "schedules"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    medicine_id: uuid.UUID = Field(foreign_key="medicines.id", nullable=False, ondelete="CASCADE")
    slot_id: uuid.UUID = Field(foreign_key="slots.id", nullable=False, ondelete="CASCADE")
    times: list = Field(sa_column=Column(JSONB, nullable=False))  # e.g. ["08:00", "20:00"]
    days_of_week: list = Field(default_factory=lambda: [1, 2, 3, 4, 5, 6, 7], sa_column=Column(JSONB, nullable=False))
    start_date: date = Field(nullable=False)
    end_date: Optional[date] = None
    every_n_days: int = Field(default=1, nullable=False)
    is_active: bool = Field(default=True, nullable=False)

    # table relations for schedule
    medicine: Medicine = Relationship(back_populates="schedules")
    slot: Slot = Relationship(back_populates="schedules")
    dose_logs: List["DoseLog"] = Relationship(back_populates="schedule", cascade_delete=True)


class DoseLog(SQLModel, table=True):
    __tablename__ = "dose_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    schedule_id: uuid.UUID = Field(foreign_key="schedules.id", nullable=False, ondelete="CASCADE")
    scheduled_at: datetime = Field(nullable=False)
    taken_at: Optional[datetime] = None
    status: str = Field(default="pending", nullable=False)  # pending, taken, missed, skipped, late
    source: Optional[str] = None  # device, app, auto

    # table relations for doseLogs
    schedule: Schedule = Relationship(back_populates="dose_logs")
    device_events: List[DeviceEvent] = Relationship(back_populates="matched_dose")



class Caregiver(SQLModel, table=True):
    __tablename__ = "caregivers"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, ondelete="CASCADE")
    caregiver_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, ondate="CASCADE") 
    notify_on_missed: bool = Field(default=True, nullable=False)


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: str = Field(primary_key=True)  
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, ondelete="CASCADE")
    type: str = Field(nullable=False)  # dose_due, dose_missed, low_supply, device_offline, caregiver_missed
    payload: dict = Field(sa_column=Column(JSONB, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    read_at: Optional[datetime] = None

    user: User = Relationship(back_populates="notifications")
