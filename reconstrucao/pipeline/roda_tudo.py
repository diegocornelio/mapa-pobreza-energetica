"""Executa o pipeline de ponta a ponta e confere contra docs/VALIDACAO.md.

O interpretador usado é o corrente, ou o apontado por PIPELINE_PYTHON. Ele precisa
ter pandas, numpy, pyarrow e geopandas. As etapas são estritamente
sequenciais: a primeira falha interrompe a execução, porque seguir adiante produz
página montada sobre arquivo de execução anterior.
"""
import subprocess, sys, time, os
from pathlib import Path
AQUI = Path(__file__).resolve().parent
VENV = os.environ.get("PIPELINE_PYTHON", sys.executable)
ETAPAS = ["01_cde.py","01b_cde_2026.py","02_tarifa.py","03a_decfec_conjunto.py",
          "03b_decfec_municipio.py","03c_continuidade_2024_2025.py","03d_continuidade_semestre.py",
          "04_territorio.py","05_domicilio.py","05b_cadunico_serie.py",
          "06a_indice_corrigido.py","06b_renda_domiciliar.py","06c_faixas_cadunico.py",
          "06d_concentracao.py","06e_distribuidora.py","07_tarifa_social.py",
          "07b_municipio_agente.py","08_geometria.py","08b_nacional_2026.py","09_payload.py","09a_painel_municipal.py",
          "10a_payload_comparacao.py","10b_payload_continuidade.py","10c_payload_agente.py",
          "05c_serie_mensal.py","10d_payload_serie.py","10e_payload_conjuntos.py",
          "build_app.py","valida_app.py"]

falta = subprocess.run(
    [VENV, "-c", "import pandas, numpy, pyarrow, geopandas"],
    capture_output=True, text=True)
if falta.returncode != 0:
    print(f"interpretador: {VENV}")
    print(f"  {(falta.stderr or '').strip().splitlines()[-1]}")
    print("  defina PIPELINE_PYTHON apontando para o Python que tem as dependencias")
    sys.exit(1)

print(f"interpretador: {VENV}\n")
ok = []
for e in ETAPAS:
    t0 = time.time()
    r = subprocess.run([VENV, str(AQUI/e)], cwd=str(AQUI), capture_output=True, text=True)
    dt = time.time()-t0
    if r.returncode != 0:
        print(f"  FALHOU  {e:36s} {dt:6.1f}s", flush=True)
        print((r.stderr or "").strip()[-2000:], flush=True)
        print(f"\n{len(ok)} de {len(ETAPAS)} etapas concluidas; interrompido em {e}")
        sys.exit(1)
    ok.append(e); print(f"  OK      {e:36s} {dt:6.1f}s", flush=True)
print(f"\n{len(ok)} de {len(ETAPAS)} etapas concluidas")
