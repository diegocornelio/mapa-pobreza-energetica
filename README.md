# IPEM - Indice de Pobreza Energetica Municipal

O IPEM estima pobreza energetica municipal por vulnerabilidades observaveis em dados abertos.

## O que responde
Onde priorizar busca ativa da Tarifa Social, melhoria da qualidade do fornecimento e regularizacao nao repressiva.

## O que nao responde
Quem e pobre em energia dentro de cada casa; quem furta energia; causalidade.

## Como reproduzir
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
python run_all.py
pytest -q

## Fontes
Ver docs/FONTES.md.

## Licencas
Codigo: MIT. Dados derivados: CC-BY 4.0.
