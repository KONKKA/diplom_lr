import enum
from sqlalchemy import BigInteger, String, Integer, ForeignKey, TIMESTAMP, JSON, Enum, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.db import Base


class User(Base):
    """
    Represents a Telegram user who can rent proxies.

    Attributes:
        id (int): Primary key.
        tg_id (int): Unique Telegram user ID.
        first_name (str): User's first name.
        last_name (Optional[str]): User's last name.
        username (Optional[str]): Telegram username.
        phone_number (str): Contact phone number.
        balance (int): User's balance, defaults to 50.
        rentals (List[ProxyRental]): List of proxy rentals by the user.
    """
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=True)
    username: Mapped[str] = mapped_column(String(64), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    balance: Mapped[int] = mapped_column(default=50)

    rentals: Mapped[list["ProxyRental"]] = relationship(back_populates="user")


class Proxy(Base):
    """
    Represents a proxy server configuration.

    Attributes:
        id (int): Primary key.
        server_id (int): Foreign key to ProxyServer.
        internal_ip (Optional[str]): Internal IP address of the proxy.
        status_id (int): Foreign key to Status.
        proxy_type_id (int): Foreign key to ProxyType.
        rentals (List[ProxyRental]): List of rentals of this proxy.
    """
    __tablename__ = 'proxies'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("proxy_servers.id"))
    internal_ip: Mapped[str] = mapped_column(String(15), nullable=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("status.id"))
    proxy_type_id: Mapped[int] = mapped_column(ForeignKey("proxy_types.id"))

    rentals: Mapped[list["ProxyRental"]] = relationship(back_populates="proxy")


class ProxyServer(Base):
    """
    Represents a proxy server with its IP address.

    Attributes:
        id (int): Primary key.
        ip (str): IP address of the proxy server.
    """
    __tablename__ = 'proxy_servers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ip: Mapped[str] = mapped_column(String(15), nullable=False)


class ProxyRental(Base):
    """
    Records an instance of a user renting a proxy.

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key to User.
        proxy_id (int): Foreign key to Proxy.
        purchase_date (datetime): Timestamp when rental was purchased.
        expire_date (datetime): Timestamp when rental expires.
        port_id (int): Foreign key to ProxyPorts.
        login (str): Login for proxy authentication.
        password (str): Password for proxy authentication.
        user (User): The user who rented the proxy.
        proxy (Proxy): The rented proxy.
    """
    __tablename__ = 'proxy_rentals'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    proxy_id: Mapped[int] = mapped_column(ForeignKey("proxies.id"))
    purchase_date: Mapped[str] = mapped_column(TIMESTAMP, nullable=False)
    expire_date: Mapped[str] = mapped_column(TIMESTAMP, nullable=False)
    port_id: Mapped[int] = mapped_column(ForeignKey("proxy_ports.id"))
    login: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[str] = mapped_column(String(50), nullable=False)

    user: Mapped["User"] = relationship(back_populates="rentals")
    proxy: Mapped["Proxy"] = relationship(back_populates="rentals")


class ProxyType(Base):
    """
    Represents a proxy type by linking operator and protocol with speed.

    Attributes:
        id (int): Primary key.
        operator_id (int): Foreign key to Operator.
        protocol_id (int): Foreign key to Protocol.
        speed (int): Proxy speed, default is 30.
    """
    __tablename__ = 'proxy_types'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operator_id: Mapped[int] = mapped_column(ForeignKey("operators.id"))
    protocol_id: Mapped[int] = mapped_column(ForeignKey("protocols.id"))
    speed: Mapped[int] = mapped_column(Integer, default=30)


class Protocol(Base):
    """
    Represents a supported proxy protocol (e.g., HTTP, SOCKS5).

    Attributes:
        id (int): Primary key.
        value (str): Protocol name.
    """
    __tablename__ = 'protocols'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    value: Mapped[str] = mapped_column(String(20), nullable=False)


class Operator(Base):
    """
    Represents a mobile or ISP operator.

    Attributes:
        id (int): Primary key.
        name (str): Operator name (e.g., Vodafone).
        country_code (str): Country code of the operator.
    """
    __tablename__ = 'operators'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)


class Status(Base):
    """
    Represents the current status of a proxy.

    Attributes:
        id (int): Primary key.
        value (str): Status name (e.g., free, occupied).
    """
    __tablename__ = 'status'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    value: Mapped[str] = mapped_column(String(20), nullable=False)


class ProxyCatalog(Base):
    """
    Represents the inventory of available proxies per proxy type.

    Attributes:
        id (int): Primary key.
        proxy_type_id (int): Foreign key to ProxyType.
        available_amount (int): Number of proxies available, default 0.
        price_per_week (int): Price per week in monetary units, default 9999.
    """
    __tablename__ = 'proxy_catalog'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    proxy_type_id: Mapped[int] = mapped_column(ForeignKey("proxy_types.id"))
    available_amount: Mapped[int] = mapped_column(Integer, default=0)
    price_per_week: Mapped[int] = mapped_column(default=9999)


class ProxyPorts(Base):
    """
    Represents ports on proxy servers.

    Attributes:
        id (int): Primary key.
        server_id (int): Foreign key to ProxyServer.
        port (int): Port number.
        status_id (int): Foreign key to Status.
    """
    __tablename__ = 'proxy_ports'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("proxy_servers.id"))
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("status.id"))


class TaskStatusEnum(str, enum.Enum):
    """
    Enum for proxy task statuses.
    """
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"


class ProxyTaskQueue(Base):
    """
    Represents tasks related to proxy management queued for processing.

    Attributes:
        id (int): Primary key.
        task_type (str): Type of the task.
        server_ip (str): IP address of the proxy server related to the task.
        payload (dict): JSON payload with task details.
        status (TaskStatusEnum): Current status of the task.
        created_at (datetime): Task creation timestamp.
        updated_at (Optional[datetime]): Timestamp of last update.
        error_message (Optional[str]): Error message if task failed.
    """
    __tablename__ = "proxy_task_queue"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    server_ip: Mapped[str] = mapped_column(String(15), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    status: Mapped[TaskStatusEnum] = mapped_column(Enum(TaskStatusEnum), default=TaskStatusEnum.pending, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    error_message: Mapped[str] = mapped_column(Text, nullable=True)
