from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


# ============================================================
# CAMERA MODEL
# ============================================================

class CameraModel(Base):

    __tablename__ = "cameras"


    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )


    # --------------------------------------------------------
    # CAMERA NAME
    # --------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )


    # --------------------------------------------------------
    # IP ADDRESS
    # --------------------------------------------------------

    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False
    )


    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="offline"
    )


    # --------------------------------------------------------
    # CAMERA TYPE
    # --------------------------------------------------------

    camera_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="IP"
    )


    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    location: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Unknown"
    )


    # --------------------------------------------------------
    # RTSP URL
    # --------------------------------------------------------

    rtsp_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )


    # --------------------------------------------------------
    # USERNAME
    # --------------------------------------------------------

    username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )


    # --------------------------------------------------------
    # DEVICE INDEX
    # Used for USB/webcam cameras
    # --------------------------------------------------------

    device_index: Mapped[int | None] = mapped_column(
        nullable=True
    )


# ============================================================
# RECORDING MODEL
# ============================================================

class RecordingModel(Base):

    __tablename__ = "recordings"


    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )


    # --------------------------------------------------------
    # CAMERA ID
    # --------------------------------------------------------

    camera_id: Mapped[int] = mapped_column(
        nullable=False
    )


    # --------------------------------------------------------
    # FILE NAME
    # --------------------------------------------------------

    filename: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )


    # --------------------------------------------------------
    # START TIME
    # PostgreSQL: timestamp
    # --------------------------------------------------------

    start_time: Mapped[datetime] = mapped_column(
        nullable=False
    )


    # --------------------------------------------------------
    # END TIME
    # PostgreSQL: timestamp
    # --------------------------------------------------------

    end_time: Mapped[datetime | None] = mapped_column(
        nullable=True
    )


    # --------------------------------------------------------
    # DURATION
    # --------------------------------------------------------

    duration_seconds: Mapped[int | None] = mapped_column(
        nullable=True
    )


    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="completed"
    )