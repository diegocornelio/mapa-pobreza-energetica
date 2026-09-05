"""Refaz todas as saidas processadas. Uso: python run_all.py"""
import subprocess
import sys

for module in ["src.prepare", "src.indicators_run", "src.validate", "src.export"]:
    print(f"== {module}")
    subprocess.run([sys.executable, "-m", module], check=True)
print("OK: data/processed atualizado")
