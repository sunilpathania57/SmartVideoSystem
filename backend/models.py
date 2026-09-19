from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class CameraModel(Base):
    __tablename__ = "cameras"

    # ---------------------------------------------------------
    # ID
    # ---------------------------------------------------------

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    # ---------------------------------------------------------
    # CAMERA NAME
    # ---------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # ---------------------------------------------------------
    # IP ADDRESS
    # ---------------------------------------------------------

    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False
    )

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="offline"
    )

    # ---------------------------------------------------------
    # CAMERA TYPE
    # Example: IP / USB / NORMAL
    # ---------------------------------------------------------

    camera_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="IP"
    )

    # ---------------------------------------------------------
    # LOCATION
    # ---------------------------------------------------------

    location: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Unknown"
    )

    # ---------------------------------------------------------
    # RTSP URL
    # Used for IP cameras
    # ---------------------------------------------------------

    rtsp_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ---------------------------------------------------------
    # USERNAME
    # Used for IP cameras
    # ---------------------------------------------------------

    username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # ---------------------------------------------------------
    # DEVICE INDEX
    # Used for USB/laptop cameras
    # Example: 0 = first webcam
    # ---------------------------------------------------------

    device_index: Mapped[int | None] = mapped_column(
        nullable=True
    )