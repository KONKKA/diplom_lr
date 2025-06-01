import enum

from sqlalchemy import BigInteger, String, Integer, ForeignKey, TIMESTAMP, JSON, Enum, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.db import Base

# Represents a Telegram user who can rent proxies
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=True)
    username: Mapped[str] = mapped_column(String(64), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    balance: Mapped[int] = mapped_column(default=50)

    # One-to-many relationship: a user can have many proxy rentals
    rentals: Mapped[list["ProxyRental"]] = relationship(back_populates="user")

# Represents a proxy server configuration
class Proxy(Base):
    __tablename__ = 'proxies'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("proxy_servers.id"))
    internal_ip: Mapped[str] = mapped_column(String(15), nullable=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("status.id"))
    proxy_type_id: Mapped[int] = mapped_column(ForeignKey("proxy_types.id"))

    # One-to-many relationship: a proxy can be rented multiple times
    rentals: Mapped[list["ProxyRental"]] = relationship(back_populates="proxy")

# Represents a proxy server ip
class ProxyServer(Base):
    __tablename__ = 'proxy_servers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ip: Mapped[str] = mapped_column(String(15), nullable=False)


# Represents a record of a user renting a proxy
class ProxyRental(Base):
    __tablename__ = 'proxy_rentals'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    proxy_id: Mapped[int] = mapped_column(ForeignKey("proxies.id"))
    purchase_date: Mapped[str] = mapped_column(TIMESTAMP, nullable=False)
    expire_date: Mapped[str] = mapped_column(TIMESTAMP, nullable=False)
    port_id: Mapped[int] = mapped_column(ForeignKey("proxy_ports.id"))
    login: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[str] = mapped_column(String(50), nullable=False)

    # Many-to-one relationships with User and Proxy
    user: Mapped["User"] = relationship(back_populates="rentals")
    proxy: Mapped["Proxy"] = relationship(back_populates="rentals")

# Represents a proxy type by linking protocol and operator with speed
class ProxyType(Base):
    __tablename__ = 'proxy_types'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operator_id: Mapped[int] = mapped_column(ForeignKey("operators.id"))
    protocol_id: Mapped[int] = mapped_column(ForeignKey("protocols.id"))
    speed: Mapped[int] = mapped_column(Integer, default=30)


# Represents supported proxy protocols (e.g., HTTP, SOCKS5)
class Protocol(Base):
    __tablename__ = 'protocols'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    value: Mapped[str] = mapped_column(String(20), nullable=False)


# Represents a mobile or ISP operator (e.g., Vodafone)
class Operator(Base):
    __tablename__ = 'operators'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)


# Represents the current status of a proxy (e.g., free, occupied)
class Status(Base):
    __tablename__ = 'status'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    value: Mapped[str] = mapped_column(String(20), nullable=False)


# Represents the inventory of available proxies per type
class ProxyCatalog(Base):
    __tablename__ = 'proxy_catalog'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    proxy_type_id: Mapped[int] = mapped_column(ForeignKey("proxy_types.id"))
    available_amount: Mapped[int] = mapped_column(Integer, default=0)
    price_per_week: Mapped[int] = mapped_column(default=9999)

class ProxyPorts(Base):
    __tablename__ = 'proxy_ports'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("proxy_servers.id"))
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("status.id"))

class TaskStatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"

class ProxyTaskQueue(Base):
    __tablename__ = "proxy_task_queue"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    server_ip: Mapped[str] = mapped_column(String(15), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    status: Mapped[TaskStatusEnum] = mapped_column(Enum(TaskStatusEnum), default=TaskStatusEnum.pending, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime,server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    error_message: Mapped[str] = mapped_column(Text, nullable=True)