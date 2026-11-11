
from pathlib import Path
from datetime import datetime
import json
import re
import unicodedata

import pandas as pd


# ============================================================
# 1. CONFIGURAÇÕES
# ============================================================

ALIASES = {
    "dispositivo": [
        "dispositivo",
        "nome do host",
        "host",
        "equipamento",
        "impressora",
    ],
    "localizacao": [
        "localizacao",
        "local",
        "unidade",
    ],
    "grupo": [
        "grupo",
        "categoria",
    ],
    "endereco_ip": [
        "endereco ip",
        "ip",
    ],
    "digitalizacao": [
        "digitalizacao",
        "digitalizacoes",
        "scans",
    ],
    "contador": [
        "total",
        "impressoes",
        "impressao",
        "contador",
    ],
    "adicionado_sistema": [
        "adicionado a sistema",
    ],
    "ultima_coleta": [
        "ultima coleta de dados bem sucedida",
        "ultima coleta",
    ],
}

COLUNAS_OBRIGATORIAS = [
    "dispositivo",
    "localizacao",
    "grupo",
    "contador",
]

EXTENSOES_SUPORTADAS = {
    ".csv",
    ".xlsx",
    ".xls",
}


# ============================================================
# 2. NORMALIZAÇÃO DE TEXTOS
# ============================================================

def normalizar_texto(valor):
    """
    Remove acentos, pontuações e espaços desnecessários.
    Padroniza textos para facilitar a identificação
    das colunas, independentemente de sua escrita.
    """

    texto = str(valor).strip().lower()

    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(r"[^a-z0-9 ]+", " ", texto)

    return re.sub(r"\s+", " ", texto).strip()


# ============================================================
# 3. PADRONIZAÇÃO DAS COLUNAS
# ============================================================

def padronizar_colunas(df):
    """
    Converte os nomes originais das colunas
    para os nomes padronizados do sistema.
    """

    aliases_normalizados = {
        normalizar_texto(alias): padrao
        for padrao, aliases in ALIASES.items()
        for alias in aliases
    }

    mapa = {}

    for coluna in df.columns:
        nome = normalizar_texto(coluna)

        mapa[coluna] = aliases_normalizados.get(
            nome,
            nome,
        )

    return df.rename(columns=mapa)


# ============================================================
# 4. LEITURA DOS ARQUIVOS
# ============================================================

def ler_arquivo(caminho):
    """
    Lê arquivos CSV ou Excel.

    Para CSV, tenta diferentes codificações,
    permitindo trabalhar com arquivos de
    diferentes origens.
    """

    extensao = caminho.suffix.lower()

    if extensao == ".csv":

        erros = []

        for encoding in [
            "utf-8-sig",
            "cp1252",
            "latin1",
        ]:

            try:

                return pd.read_csv(
                    caminho,
                    sep=None,
                    engine="python",
                    encoding=encoding,
                )

            except Exception as erro:

                erros.append(
                    f"{encoding}: {erro}"
                )

        raise ValueError(
            "Não foi possível ler o CSV. "
            + " | ".join(erros)
        )

    if extensao in [".xlsx", ".xls"]:

        return pd.read_excel(caminho)

    raise ValueError(
        f"Formato não suportado: {extensao}"
    )


# ============================================================
# 5. IDENTIFICAÇÃO DA COMPETÊNCIA
# ============================================================

def identificar_competencia(nome_arquivo):
    """
    Identifica ano e mês pelo nome do arquivo.

    Padrão esperado: AAAA-MM

    Exemplo: 2025-01.csv
    """

    resultado = re.match(
        r"^(\d{4})-(\d{2})$",
        Path(nome_arquivo).stem,
    )

    if not resultado:

        raise ValueError(
            "Nome inválido. Utilize o padrão AAAA-MM."
        )

    ano = int(resultado.group(1))
    mes = int(resultado.group(2))

    if not 1 <= mes <= 12:

        raise ValueError(
            f"Mês inválido: {mes}"
        )

    return ano, mes


# ============================================================
# 6. VERIFICAÇÃO DE CAMPOS VAZIOS
# ============================================================

def contar_valores_vazios(serie):
    """
    Conta valores nulos ou textos vazios.
    """

    vazios = serie.isna()

    textos_vazios = (
        serie.astype("string")
        .str.strip()
        .eq("")
        .fillna(False)
    )

    return int((vazios | textos_vazios).sum())


# ============================================================
# 7. INSPEÇÃO INDIVIDUAL DOS ARQUIVOS
# ============================================================

def inspecionar_arquivo(caminho):
    """
    Executa o diagnóstico de um arquivo mensal.

    Verifica:
    - Estrutura das colunas.
    - Campos obrigatórios.
    - Contadores inválidos.
    - Contadores negativos.
    - Registros duplicados.
    - Quantidade de equipamentos.
    - Total de impressões.
    """

    resultado = {
        "arquivo": caminho.name,
        "status": "erro",
        "problemas": [],
    }

    try:

        # Identifica a competência
        ano, mes = identificar_competencia(
            caminho.name
        )

        resultado["ano"] = ano
        resultado["mes"] = mes

        # Lê e padroniza o arquivo
        df = ler_arquivo(caminho)

        df = padronizar_colunas(df)

        resultado["colunas"] = list(df.columns)

        resultado["quantidade_registros"] = len(df)

        # Verifica se existem colunas obrigatórias
        ausentes = [
            coluna
            for coluna in COLUNAS_OBRIGATORIAS
            if coluna not in df.columns
        ]

        if ausentes:

            resultado["problemas"].append(
                "Colunas obrigatórias ausentes: "
                f"{ausentes}"
            )

            return resultado

        # Verifica arquivo sem registros
        if df.empty:

            resultado["problemas"].append(
                "Arquivo sem registros."
            )

            return resultado

        # ----------------------------------------------------
        # Normalização dos identificadores
        # ----------------------------------------------------

        df["dispositivo"] = (
            df["dispositivo"]
            .astype("string")
            .str.strip()
        )

        # ----------------------------------------------------
        # Validação dos contadores
        # ----------------------------------------------------

        df["contador_original"] = df["contador"]

        df["contador"] = pd.to_numeric(
            df["contador"],
            errors="coerce",
        )

        invalidos = int(
            df["contador"].isna().sum()
        )

        negativos = int(
            (df["contador"] < 0).sum()
        )

        if invalidos:

            resultado["problemas"].append(
                f"{invalidos} registros com "
                "contador inválido."
            )

        if negativos:

            resultado["problemas"].append(
                f"{negativos} registros com "
                "contador negativo."
            )

        # ----------------------------------------------------
        # Verificação de campos obrigatórios vazios
        # ----------------------------------------------------

        for coluna in COLUNAS_OBRIGATORIAS:

            vazios = contar_valores_vazios(
                df[coluna]
            )

            if vazios:

                resultado["problemas"].append(
                    f"{vazios} registros sem "
                    f"preenchimento em {coluna}."
                )

        # ----------------------------------------------------
        # Verificação de dispositivos duplicados
        # ----------------------------------------------------

        identificadores_validos = (
            df["dispositivo"].notna()
            & df["dispositivo"].str.strip().ne("")
        )

        dispositivos = df.loc[
            identificadores_validos,
            "dispositivo",
        ]

        duplicados = int(
            dispositivos.duplicated(
                keep=False
            ).sum()
        )

        if duplicados:

            resultado["problemas"].append(
                f"{duplicados} registros envolvidos "
                "em duplicidade de dispositivo."
            )

        # ----------------------------------------------------
        # Cálculo do total de impressões
        # ----------------------------------------------------

        total = df["contador"].sum()

        if invalidos or negativos:

            total = None

        elif pd.notna(total):

            total = int(total)

        # ----------------------------------------------------
        # Consolidação do resultado
        # ----------------------------------------------------

        resultado.update({

            "total_impressoes": total,

            "equipamentos_distintos": int(
                dispositivos.nunique()
            ),

            "registros_duplicados": duplicados,

            "contadores_invalidos": invalidos,

            "contadores_negativos": negativos,

        })

        resultado["status"] = (
            "alerta"
            if resultado["problemas"]
            else "ok"
        )

    except Exception as erro:

        resultado["status"] = "erro"

        resultado["problemas"].append(
            str(erro)
        )

    return resultado


# ============================================================
# 8. DIAGNÓSTICO DE TODOS OS ARQUIVOS
# ============================================================

def gerar_diagnostico(
    pasta_dados,
    pasta_saida,
):
    """
    Percorre a pasta de dados, inspeciona todos
    os arquivos e gera um relatório JSON.

    Também identifica competências ausentes.
    """

    pasta_dados = Path(pasta_dados)

    pasta_saida = Path(pasta_saida)

    pasta_saida.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Localização dos arquivos
    # --------------------------------------------------------

    arquivos = sorted(

        arquivo

        for arquivo in pasta_dados.iterdir()

        if arquivo.is_file()

        and arquivo.suffix.lower()
        in EXTENSOES_SUPORTADAS

    )

    # --------------------------------------------------------
    # Inspeção individual
    # --------------------------------------------------------

    resultados = [

        inspecionar_arquivo(arquivo)

        for arquivo in arquivos

    ]

    # --------------------------------------------------------
    # Identificação das competências existentes
    # --------------------------------------------------------

    competencias = set()

    for resultado in resultados:

        if (
            "ano" in resultado
            and "mes" in resultado
        ):

            competencias.add(
                (
                    resultado["ano"],
                    resultado["mes"],
                )
            )

    # --------------------------------------------------------
    # Identificação das competências ausentes
    # --------------------------------------------------------

    meses_ausentes = []

    if competencias:

        primeira = min(competencias)

        ultima = max(competencias)

        inicio = pd.Period(
            year=primeira[0],
            month=primeira[1],
            freq="M",
        )

        fim = pd.Period(
            year=ultima[0],
            month=ultima[1],
            freq="M",
        )

        esperadas = pd.period_range(
            inicio,
            fim,
            freq="M",
        )

        meses_ausentes = [

            str(periodo)

            for periodo in esperadas

            if (
                periodo.year,
                periodo.month,
            ) not in competencias

        ]

    # --------------------------------------------------------
    # Consolidação do diagnóstico
    # --------------------------------------------------------

    relatorio = {

        "gerado_em": datetime.now().isoformat(
            timespec="seconds"
        ),

        "pasta_analisada": str(
            pasta_dados
        ),

        "total_arquivos": len(arquivos),

        "arquivos_ok": sum(
            r["status"] == "ok"
            for r in resultados
        ),

        "arquivos_com_alertas": sum(
            r["status"] == "alerta"
            for r in resultados
        ),

        "arquivos_com_erro": sum(
            r["status"] == "erro"
            for r in resultados
        ),

        "competencias_ausentes": meses_ausentes,

        "arquivos": resultados,

    }

    # --------------------------------------------------------
    # Geração do relatório JSON
    # --------------------------------------------------------

    destino = (
        pasta_saida
        / "diagnostico.json"
    )

    with destino.open(
        "w",
        encoding="utf-8",
    ) as arquivo:

        json.dump(
            relatorio,
            arquivo,
            ensure_ascii=False,
            indent=4,
        )

    # --------------------------------------------------------
    # Exibição do resultado no terminal
    # --------------------------------------------------------

    print(
        "\n===== DIAGNÓSTICO PRINT CONTROL ====="
    )

    print(
        f"Arquivos encontrados: "
        f"{relatorio['total_arquivos']}"
    )

    print(
        f"Arquivos OK: "
        f"{relatorio['arquivos_ok']}"
    )

    print(
        f"Arquivos com alertas: "
        f"{relatorio['arquivos_com_alertas']}"
    )

    print(
        f"Arquivos com erros: "
        f"{relatorio['arquivos_com_erro']}"
    )

    print(
        f"Competências ausentes: "
        f"{len(meses_ausentes)}"
    )

    if meses_ausentes:

        print(
            "Meses ausentes: "
            + ", ".join(meses_ausentes)
        )

    print(
        f"\nRelatório salvo em: {destino}"
    )

    return relatorio
