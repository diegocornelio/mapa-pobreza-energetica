# IPEM: Índice de Pobreza Energética Municipal

O IPEM estima pobreza energética municipal por vulnerabilidades observáveis em dados abertos.

## O que responde
Onde priorizar busca ativa da Tarifa Social, melhoria da qualidade do fornecimento e regularização não repressiva.

## O que nao responde
Quem é pobre em energia dentro de cada casa; quem furta energia; causalidade.

## Como reproduzir
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
python run_all.py
pytest -q

## Fontes
Ver docs/FONTES.md.

## Licencas
Código: MIT. Dados derivados: CC-BY 4.0.

## Sobre o autor

Diego H. C. de Rezende é fundador da Struktur Energia. Engenheiro de Computação e mestre em Engenharia de Software, tem experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).
