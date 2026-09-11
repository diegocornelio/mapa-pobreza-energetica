"""Caminhos do pipeline de reconstrução do Mapa da Pobreza Energética.

RAW aponta para o diretório de dados brutos baixados em 2026-09-05.
Ele NÃO acompanha o repositório: são cerca de 3 GB, com um CSV de 2,3 GB
dentro do zip da CDE. As URLs de origem estão em data/sources/fontes.csv.

Onde esses 3 GB ficam é específico de cada instalação, então o caminho não é
escrito aqui. Ele é procurado em três lugares, nesta ordem: um módulo
`_paths_local.py` ao lado deste, que não acompanha o repositório; as variáveis de
ambiente IPEM_RAW e IPEM_INTERIM; e, por último, `data/raw` e `data/interim` dentro
do próprio repositório. Quem clonar precisa apenas apontar para a sua cópia, por
qualquer um dos três caminhos, e nenhum layout de disco alheio vem junto.
"""
import os
from pathlib import Path

_BASE = Path(__file__).resolve().parents[2]
try:
    from _paths_local import RAW, INTERIM_ORIG
except ImportError:
    RAW = Path(os.environ.get("IPEM_RAW", _BASE / "data" / "raw"))
    INTERIM_ORIG = Path(os.environ.get("IPEM_INTERIM", _BASE / "data" / "interim"))
PROCESSED_ORIG = Path(__file__).resolve().parents[2] / "data" / "processed" / "ipem_municipios.csv"
OUT = Path(__file__).resolve().parents[1] / "dados"
OUT.mkdir(parents=True, exist_ok=True)

# --- data de referencia da leitura do presente -------------------------------
# A tarifa homologada e o parque de unidades consumidoras acompanham a mesma data
# do CadUnico e da CDE. Enquanto esta data vivia espalhada por quatro arquivos,
# foi possivel escrever na legenda do aplicativo que a tarifa era de marco de 2026
# enquanto o calculo usava dezembro de 2024, e nada acusou.
REF_TARIFA = "2026-03-01"
ANO_UC = 2026

# --- valores nominais de renda, com a data em que passaram a valer ------------
# Os dois sao fixados em ato do Executivo e NAO sao indexados: ficam parados em
# termos nominais ate que um novo ato os mude. A tarifa, ao contrario, e
# reajustada todo ano. E por isso que o peso da conta na renda sobe entre duas
# leituras sem que nenhuma familia tenha empobrecido: o numerador e corrigido e o
# denominador nao. Quem mover REF_TARIFA tem de conferir estes dois na mesma data.
LINHA_POBREZA = 218.0          # por pessoa ao mes, teto da faixa de pobreza do CadUnico
LINHA_POBREZA_VIGENCIA = "2023-06-16"   # Decreto 11.566/2023; sem reajuste ate REF_TARIFA
SALARIO_MINIMO = 1621.0        # teto da faixa de baixa renda e meio salario minimo
SALARIO_MINIMO_VIGENCIA = "2026-01-01"  # Decreto 12.797/2025

# --- bandeiras tarifarias ----------------------------------------------------
# Adicional por kWh consumido, uniforme no pais, cobrado por fora da tarifa
# homologada. E o canal de curto prazo pelo qual a hidrologia chega a conta: seca
# eleva o despacho termico, o custo sobe e a bandeira acompanha. A tarifa que este
# projeto usa NAO inclui bandeira, entao a conta publicada e piso.
# Fonte: ANEEL, pagina de bandeiras tarifarias, lida em 2026-09-11.
BANDEIRAS = {"verde": 0.0, "amarela": 0.01885,
             "vermelha1": 0.04463, "vermelha2": 0.07877}
BANDEIRAS_FONTE = "ANEEL, bandeiras tarifarias, pagina atualizada em 2026-01-08"
