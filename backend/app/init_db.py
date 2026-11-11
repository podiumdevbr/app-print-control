
from app.core.database import Base, DATABASE_DIR, DATABASE_URL, engine
from app import models  # noqa: F401


def initialize_database():
    """Cria as tabelas do banco caso ainda não existam."""

    Base.metadata.create_all(bind=engine)

    print("======================================")
    print(" PRINT CONTROL - BANCO DE DADOS")
    print("======================================")
    print("Banco inicializado com sucesso.")
    print(f"Diretório: {DATABASE_DIR}")
    print(f"Conexão: {DATABASE_URL}")
    print("Tabelas criadas ou verificadas:")
    
    for table_name in Base.metadata.tables:
        print(f" - {table_name}")

    print("======================================")


if __name__ == "__main__":
    initialize_database()
