
from pathlib import Path

from app.services.data_inspector import gerar_diagnostico


# Raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent

# Diretórios de entrada e saída
PASTA_RAW = ROOT_DIR / "data" / "raw"
PASTA_PROCESSED = ROOT_DIR / "data" / "processed"


if __name__ == "__main__":
    if not PASTA_RAW.exists():
        raise FileNotFoundError(
            f"Pasta de dados não encontrada: {PASTA_RAW}"
        )

    gerar_diagnostico(
        pasta_dados=PASTA_RAW,
        pasta_saida=PASTA_PROCESSED,
    )
