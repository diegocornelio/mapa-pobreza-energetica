import pandas as pd, numpy as np, json, os
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
d=pd.read_csv(str(OUT)+"/app_dados2.csv")
dist=sorted(d.distribuidora.dropna().unique().tolist()); di={v:i for i,v in enumerate(dist)}
def col(s,dec=None):
    if dec is None: return [None if pd.isna(x) else int(x) for x in s]
    return [None if pd.isna(x) else round(float(x),dec) for x in s]
out={"n":len(d),"dist":dist,
  "cod":d.cod_ibge.tolist(),"nome":d.nome.tolist(),"uf":d.uf.tolist(),"di":[di[x] for x in d.distribuidora],
  "cad":col(d.familias_cadastradas),"pob":col(d.familias_pobreza),"bxr":col(d.familias_baixa_renda),
  # A leitura do presente e casada em marco de 2026 nas duas pontas; as colunas de
  # dezembro de 2024 seguem no payload por 10a, para a pagina de comparacao.
  "ele":col(d.familias_elegiveis_mar26),"ben":col(d.beneficiarios_mar26),
  "eleCecad":col(d.familias_elegiveis),"benDez24":col(d.beneficiarios_tsee),
  "cob":col(d.cobertura,1),"lac":col(d.lacuna_pos),"sob":col(d.sobrecobertura),
  "rs":col(d.rs_nao_acessado,0),"spf":col(d.subsidio_familia_mar26,2),"sind":col(d.subsidio_indisponivel),
  "tar":col(d.tarifa_municipal,4),"tas":col(d.tarifa_baixa_renda,4),"rkt":col(d.rank_tarifa),
  "hh":col(d.moradores_por_domicilio,2),
  "pc":col(d.peso_pob80_cheia,4),"ps":col(d.peso_social_ef,4),
  "cc":col(d.conta_cheia80,2),"cs":col(d.conta_social80,2),"ec":col(d.econ_mes,2),
  "dec":col(d.dec_h_ano,1),"d3":col(d.d3_corr,3),"d3x":col(d.d3_max,2),"nc":col(d.n_conj),
  "vio":col(d.violacao),"fav":col(d.dom_favela),"dt":col(d.dom_total_mun),"pf":col(d.d4_corr,4),
  "fm":[1 if x else 0 for x in d.favela_mapeada],"ren":col(d.renda_referencia,0)}
open(str(OUT)+"/dados.json","w",encoding="utf-8").write(json.dumps(out,separators=(",",":"),ensure_ascii=False))
print("dados.json: %.2f MB"%(os.path.getsize(str(OUT)+"/dados.json")/1e6))
print("checagem Nova Iguacu:")
r=d[d.cod_ibge==3303500].iloc[0]
print(f"  conta cheia R$ {r.conta_cheia80:.2f} -> social R$ {r.conta_social80:.2f} | economia R$ {r.econ_mes:.2f}/mes")
print(f"  peso {100*r.peso_pob80_cheia:.1f}% -> {100*r.peso_social_ef:.1f}%")
