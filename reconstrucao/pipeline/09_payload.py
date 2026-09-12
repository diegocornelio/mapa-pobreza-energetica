import pandas as pd, numpy as np, json, os
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import (RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT,
                    LINHA_POBREZA, LINHA_POBREZA_VIGENCIA,
                    BANDEIRAS, BANDEIRAS_FONTE)
d=pd.read_csv(str(OUT)+"/app_dados2.csv")
dist=sorted(d.distribuidora.dropna().unique().tolist()); di={v:i for i,v in enumerate(dist)}

def _narrativa(d):
    """Agregados citados em texto na tela, calculados uma vez e publicados."""
    den = LINHA_POBREZA * d.moradores_por_domicilio
    peso = lambda k: float(100*(d.tarifa_municipal*k/den).median())
    ki = (d.subsidio_familia_mar26/d.tarifa_baixa_renda).replace([np.inf,-np.inf],np.nan).dropna()
    ki = ki[ki > 0]
    return {"p30": round(peso(30),2), "p100": round(peso(100),2),
            "kimp": round(float(ki.median()),1),
            "kimpP10": round(float(ki.quantile(.10)),1),
            "kimpP90": round(float(ki.quantile(.90)),1),
            "kimpPct": round(float(100*(ki<=80).mean()),1)}
def col(s,dec=None):
    if dec is None: return [None if pd.isna(x) else int(x) for x in s]
    return [None if pd.isna(x) else round(float(x),dec) for x in s]
# A linha de pobreza vai no payload, e nao escrita a mao no JavaScript: o peso da
# conta na renda e calculado ao vivo na tela, e enquanto o valor vivia em seis
# lugares do template nada garantia que a tela e o pipeline usassem o mesmo numero.
out={"n":len(d),"dist":dist,"lp":LINHA_POBREZA,"lpv":LINHA_POBREZA_VIGENCIA,
  # A bandeira e adicional por kWh cobrado por fora da tarifa homologada, entao
  # nao entra em tar nem em cc: vai como constante para a tela montar o cenario
  # sem que o numero publicado da conta mude.
  "bnd":BANDEIRAS,"bndf":BANDEIRAS_FONTE,
  # Numeros que a prosa do aplicativo cita e que sao resultado de calculo. Ficam
  # aqui, e nao escritos a mao no template, porque frase envelhece em silencio: a
  # pagina do metodo afirmou por semanas uma sobrecobertura de 80 municipios que
  # ja era 35. valida_app.py recusa literal calculado no template justamente para
  # forcar a passagem por aqui.
  "nar":_narrativa(d),
  "cod":d.cod_ibge.tolist(),"nome":d.nome.tolist(),"uf":d.uf.tolist(),# Um municipio pode nao ter registro no INDGER da data de referencia (Acegua, RS,
  # em marco de 2026). O indice sai nulo, e a tela diz que nao sabe, em vez de o
  # pipeline quebrar ou de atribuir a distribuidora errada.
  "di":[None if pd.isna(x) else di[x] for x in d.distribuidora],
  "cad":col(d.familias_cadastradas),"pob":col(d.familias_pobreza),"bxr":col(d.familias_baixa_renda),
  # A leitura do presente e casada em marco de 2026 nas duas pontas; as colunas de
  # dezembro de 2024 seguem no payload por 10a, para a pagina de comparacao.
  "ele":col(d.familias_elegiveis_mar26),"ben":col(d.beneficiarios_mar26),
  "eleCecad":col(d.familias_elegiveis),"benDez24":col(d.beneficiarios_tsee),
  "cob":col(d.cobertura,1),"lac":col(d.lacuna_pos),"sob":col(d.sobrecobertura),
  "rs":col(d.rs_nao_acessado,0),"spf":col(d.subsidio_familia_mar26,2),"sind":col(d.subsidio_indisponivel),
  "tar":col(d.tarifa_municipal,4),"tas":col(d.tarifa_baixa_renda,4),"rkt":col(d.rank_tarifa),
  # hh, pc e ps saem com casas a mais do que a tela exibe: com duas casas em hh, o
  # recalculo ao vivo do peso cruzava o limiar de 10% em 6 municipios diferentes dos
  # que o pipeline conta. A precisao publicada tem de bastar para a decisao, e nao
  # apenas para a exibicao.
  "hh":col(d.moradores_por_domicilio,4),
  "pc":col(d.peso_pob80_cheia,6),"ps":col(d.peso_social_ef,6),
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
