
import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Raiz do projeto: app-print-control/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Diretório onde o banco será armazenado
DATABASE_DIR = PROJECT_ROOT / "data" / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DATABASE_URL = (
    f"sqlite:///{(DATABASE_DIR / 'print_control.db').as_posix()}"
)

# Permite configurar outro banco futuramente por variável de ambiente
DATABASE_URL = os.getenv(
    "PRINT_CONTROL_DATABASE_URL",
    DEFAULT_DATABASE_URL,
)


class Base(DeclarativeBase):
    """Classe-base dos modelos do banco de dados."""

    pass


# SQLite precisa dessa configuração para permitir o uso
# da conexão em diferentes threads da aplicação.
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)


# Garante que as chaves estrangeiras sejam respeitadas pelo SQLite.
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db():
    """Disponibiliza uma sessão do banco e garante seu fechamento."""

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
