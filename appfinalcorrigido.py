# ============================================================
# Shopee Premium – Viabilidade de Projeto (CAPEX adicional sobre CTO real)
# FINAL – BRL/USD + FX + horizonte + desconto + CTO detalhado e total
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

# ---------------------------
# Page / CSS (dark Shopee)
# ---------------------------
st.set_page_config(page_title="Shopee – Viabilidade Projeto", layout="wide")

CSS = """
<style>
html, body { background-color: #0f0f0f; }
.big-title {
    background: #EE4D2D; padding: 18px 20px; border-radius: 12px;
    color: white; font-weight: 900; font-size: 26px; margin-bottom: 16px;
}
.card {
    background: #191919; padding: 18px; border-radius: 14px;
    border: 1px solid #2b2b2b; box-shadow: 0 3px 12px rgba(0,0,0,0.35);
    margin-bottom: 10px;
}
.section-title {
    font-size: 22px; font-weight: 750; color: #f0f0f0;
    margin-top: 18px; margin-bottom: 8px;
}
.small { color: #a8a8a8; font-size: 13px; }
.stButton>button, .stDownloadButton>button {
    background: #EE4D2D !important; color: white !important; border-radius: 10px !important;
    font-weight: bold !important; border: none !important; padding: 8px 14px !important;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    '<div class="big-title">🧮 Viabilidade Econômica – Projeto Catraca + Facial (Shopee)</div>',
    unsafe_allow_html=True
)

# ---------------------------
# Helpers
# ---------------------------
def brl_fmt(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")

def usd_fmt(v):
    return f"${v:,.2f}"

def to_brl(v, moeda, fx):
    return v if moeda == "BRL" else v * fx

def from_brl(v, moeda, fx):
    return v if moeda == "BRL" else v / fx

def fmt(v_brl, moeda, fx):
    v = from_brl(v_brl, moeda, fx)
    return brl_fmt(v) if moeda == "BRL" else usd_fmt(v)

def npv(rate_m, cashflows):
    return sum(cf / ((1 + rate_m) ** t) for t, cf in enumerate(cashflows))

def irr_safe(cashflows):
    # IRR precisa ter pelo menos um fluxo positivo e um negativo.
    if not (any(cf > 0 for cf in cashflows) and any(cf < 0 for cf in cashflows)):
        return None
    try:
        return np.irr(cashflows)
    except Exception:
        return None

def cumulative(v):
    return np.cumsum(v)

# ---------------------------
# Sidebar – global configs
# ---------------------------
st.sidebar.header("⚙️ Configurações")

moeda = st.sidebar.selectbox(
    "Moeda de entrada/saída",
    ["BRL", "USD"],
    help="Se USD, todos os inputs devem ser em USD; a base interna é BRL."
)

if moeda == "USD":
    fx_rate = 5.25
    st.sidebar.caption("FX fixo USD/BRL: 5.25")
else:
    fx_rate = st.sidebar.number_input("Cotação USD/BRL", min_value=1.0, value=5.25, step=0.05)

horizon = st.sidebar.slider("Horizonte de diluição (meses)", 6, 84, 36, step=6)

taxa_anual = st.sidebar.number_input("Taxa de desconto anual (%)", 0.0, 60.0, 12.0, step=0.5)
taxa_mensal = (1 + taxa_anual/100) ** (1/12) - 1

cenario = st.sidebar.selectbox("Cenário de preços CAPEX", ["Base", "Otimista", "Pessimista"])
sc_mult = {"Base":1.0, "Otimista":0.9, "Pessimista":1.1}[cenario]

st.sidebar.divider()
st.sidebar.caption("Modelo: CTO atual real + CAPEX adicional diluído no horizonte. Sem economia mensurável.")

# ============================================================
# 1) Inputs dos Hubs
# ============================================================
st.markdown('<div class="section-title">1) Inputs da Operação</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    hubs_lm = c1.number_input("Qtd Hubs LM", 0, 500, 0, step=1)
    hubs_fm = c2.number_input("Qtd Hubs FM", 0, 500, 1, step=1)
    metragem_media = c3.number_input("Metragem média por HUB (m²)", 0, 50000, 3500, step=100)

    total_hubs = hubs_lm + hubs_fm
    if total_hubs == 0:
        st.warning("Adicione pelo menos 1 hub.")
        st.stop()

    metragem_total = metragem_media * total_hubs
    st.markdown(
        f'<div class="small">Total hubs: <b>{total_hubs}</b> | '
        f'Metragem total: <b>{metragem_total:,.0f} m²</b></div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 2) CTO atual real (Opção C)
# ============================================================
st.markdown('<div class="section-title">2) CTO Atual Real (já praticado)</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    use_detailed = st.checkbox("Usar CTO detalhado por item", value=True)

    st.caption("Preencha valores MÉDIOS mensais por HUB na moeda selecionada.")

    fields = [
        "cleaning","condo","condo_utilities","engagement","hse","insurance",
        "iptu","maintenance","regulatory","rental","security","services","toilets","utilities"
    ]

    cols = st.columns(3)
    detailed_vals_brl = {}
    for i, f in enumerate(fields):
        col = cols[i % 3]
        v_in = col.number_input(
            f"{f} ({moeda}/hub mês)",
            0.0, 2_000_000.0, 0.0, step=100.0, key=f"d_{f}"
        )
        detailed_vals_brl[f] = to_brl(v_in, moeda, fx_rate)

    cto_total_hub_det_brl = sum(detailed_vals_brl.values())
    cto_total_det_brl = cto_total_hub_det_brl * total_hubs

    st.divider()
    st.caption("Alternativa: insira o CTO total mensal já consolidado (empresa).")
    cto_total_in = st.number_input(
        f"CTO total mensal consolidado ({moeda})",
        0.0, 50_000_000.0, 0.0, step=1000.0, key="cto_total_consol"
    )
    cto_total_consol_brl = to_brl(cto_total_in, moeda, fx_rate)

    cto_base_brl = cto_total_det_brl if use_detailed else cto_total_consol_brl

    k1, k2, k3 = st.columns(3)
    k1.metric("CTO por HUB (detalhado)", fmt(cto_total_hub_det_brl, moeda, fx_rate))
    k2.metric("CTO total (detalhado)", fmt(cto_total_det_brl, moeda, fx_rate))
    k3.metric("CTO base usado na análise", fmt(cto_base_brl, moeda, fx_rate))

    if not use_detailed and cto_total_consol_brl == 0:
        st.warning("Você selecionou CTO consolidado, mas ainda está zero.")

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 3) CAPEX do projeto (kit MVP)  ✅ CORRIGIDO BRL/USD
# ============================================================
st.markdown('<div class="section-title">3) CAPEX do Projeto – Kit Catraca + Facial</div>', unsafe_allow_html=True)

catalogo = pd.DataFrame([
    ["T00377","CATRACA PEDESTAL",2,8328.41],
    ["T00700","LEITOR FACIAL",4,2859.35],
    ["T00379","SUPORTE FACIAL - CATRACA",4,501.24],
    ["T00512","PORTINHOLA",1,5454.65],
], columns=["ITEM","DESCRIÇÃO","Qtd_por_Hub","Preço_CAPEX_BRL"])

# Ajuste de cenário sempre em BRL base
catalogo["Preço_CAPEX_BRL"] = catalogo["Preço_CAPEX_BRL"] * sc_mult

# Converter preço exibido conforme moeda selecionada
catalogo["Preço_CAPEX"] = from_brl(catalogo["Preço_CAPEX_BRL"], moeda, fx_rate)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.caption("Edite quantidades por HUB e preços (se necessário).")
    kit = st.data_editor(
        catalogo[["ITEM","DESCRIÇÃO","Qtd_por_Hub","Preço_CAPEX"]],
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

kit = pd.DataFrame(kit).fillna(0)

# Converter o preço editado de volta para BRL base para cálculo
kit["Preço_CAPEX_BRL"] = to_brl(kit["Preço_CAPEX"], moeda, fx_rate)

kit["CAPEX_por_Hub_brl"] = kit["Qtd_por_Hub"] * kit["Preço_CAPEX_BRL"]
kit["CAPEX_total_brl"] = kit["CAPEX_por_Hub_brl"] * total_hubs
capex_equip_brl = kit["CAPEX_total_brl"].sum()

# ============================================================
# 4) Instalação
# ============================================================
st.markdown('<div class="section-title">4) Instalação do Projeto</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    i1, i2, i3 = st.columns(3)
    cabo_in = i1.number_input(f"Cabeamento ({moeda}/m)", 0.0, 500.0, 12.0, step=1.0)
    infra_in = i2.number_input(f"Infraestrutura ({moeda}/m)", 0.0, 500.0, 8.0, step=1.0)
    mo_in = i3.number_input(f"Mão de obra ({moeda}/m)", 0.0, 500.0, 5.0, step=1.0)

    cabo_brl = to_brl(cabo_in, moeda, fx_rate)
    infra_brl = to_brl(infra_in, moeda, fx_rate)
    mo_brl = to_brl(mo_in, moeda, fx_rate)

    instal_brl = (cabo_brl + infra_brl + mo_brl) * metragem_media * total_hubs

    st.metric("Instalação total", fmt(instal_brl, moeda, fx_rate))
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 5) Consolidação CAPEX
# ============================================================
capex_total_brl = capex_equip_brl + instal_brl

st.markdown('<div class="section-title">5) Consolidação CAPEX do Projeto</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    a1, a2, a3 = st.columns(3)
    a1.metric("CAPEX Equipamentos", fmt(capex_equip_brl, moeda, fx_rate))
    a2.metric("CAPEX Instalação", fmt(instal_brl, moeda, fx_rate))
    a3.metric("CAPEX Total Projeto", fmt(capex_total_brl, moeda, fx_rate))
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 6) Diluição do CAPEX e impacto no CTO
# ============================================================
st.markdown('<div class="section-title">6) Diluição e Impacto no CTO</div>', unsafe_allow_html=True)

cto_add_mensal_brl = capex_total_brl / horizon
cto_novo_brl = cto_base_brl + cto_add_mensal_brl

share_pct = (cto_add_mensal_brl / cto_base_brl * 100) if cto_base_brl > 0 else np.nan

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("CTO atual (base)", fmt(cto_base_brl, moeda, fx_rate))
    b2.metric("CTO adicional projeto/mês", fmt(cto_add_mensal_brl, moeda, fx_rate))
    b3.metric("CTO novo total/mês", fmt(cto_novo_brl, moeda, fx_rate))
    b4.metric("Impacto % no CTO", f"{share_pct:.2f}%" if np.isfinite(share_pct) else "N/A")

    st.caption(
        f"O CAPEX de {fmt(capex_total_brl, moeda, fx_rate)} "
        f"será diluído em {horizon} meses → "
        f"equivale a {fmt(cto_add_mensal_brl, moeda, fx_rate)} adicionais por mês."
    )

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 7) Indicadores financeiros (sem economia mensurável)
# ============================================================
st.markdown('<div class="section-title">7) Indicadores Financeiros do Projeto</div>', unsafe_allow_html=True)

cf_proj = [-capex_total_brl] + [0.0] * horizon
vpl_proj_brl = npv(taxa_mensal, cf_proj)
tir_real_m = irr_safe(cf_proj)
tir_real_a = ((1 + tir_real_m) ** 12 - 1) if tir_real_m is not None else None
payback_dilutivo = horizon

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    p1.metric("Payback (dilutivo)", f"{payback_dilutivo} meses")
    p2.metric("VPL do Projeto", fmt(vpl_proj_brl, moeda, fx_rate))
    p3.metric("TIR real (anual)", f"{tir_real_a*100:.1f}%" if tir_real_a is not None else "N/A")

    st.caption(
        "Sem economias mensuráveis, TIR/VPL não representam retorno financeiro clássico "
        "(apenas o custo presente do investimento)."
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 8) Conclusão executiva automática
# ============================================================
st.markdown('<div class="section-title">8) Conclusão de Viabilidade (Impacto no CTO)</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    if np.isfinite(share_pct):
        if share_pct < 3:
            st.success("✅ Baixo impacto financeiro no CTO. Projeto recomendado.")
            st.write(
                f"O projeto adiciona ~{share_pct:.2f}% ao CTO mensal. "
                "Impacto facilmente absorvível pela operação; viabilidade econômica alta "
                "para objetivos de segurança/compliance."
            )
        elif share_pct < 10:
            st.warning("🟠 Impacto moderado no CTO. Recomendável com justificativa operacional.")
            st.write(
                f"O projeto aumenta o CTO em ~{share_pct:.2f}%. "
                "Viável se os ganhos indiretos (segurança, controle de acesso, risco) "
                "forem considerados prioritários."
            )
        else:
            st.error("🟥 Alto impacto no CTO. Projeto exige forte justificativa e/ou otimização.")
            st.write(
                f"O projeto adiciona ~{share_pct:.2f}% ao CTO mensal. "
                "Impacto relevante; recomenda-se revisar escopo, preços, instalação "
                "ou fasear a implementação."
            )
    else:
        st.info("CTO base está zero ou não informado — não foi possível calcular share.")

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 9) Gráficos
# ============================================================
st.markdown('<div class="section-title">9) Gráficos</div>', unsafe_allow_html=True)

meses = np.arange(0, horizon + 1)
cto_atual_series = np.repeat(cto_base_brl, horizon + 1)
cto_novo_series = cto_atual_series + np.concatenate([[0], np.repeat(cto_add_mensal_brl, horizon)])

g1, g2 = st.columns(2)

with g1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("**CTO mensal: atual vs com projeto (diluído)**")
    fig, ax = plt.subplots()
    ax.plot(meses, cto_atual_series, label="CTO atual")
    ax.plot(meses, cto_novo_series, label="CTO com projeto")
    ax.set_xlabel("Meses")
    ax.set_ylabel("CTO (BRL base)")
    ax.legend()
    st.pyplot(fig)
    st.markdown('</div>', unsafe_allow_html=True)

with g2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("**Custo acumulado do CAPEX diluído**")
    capex_cum = cumulative([capex_total_brl] + [0]*horizon)
    cto_add_cum = cumulative([0] + [cto_add_mensal_brl]*horizon)
    fig2, ax2 = plt.subplots()
    ax2.plot(meses, capex_cum, label="CAPEX acumulado (M0)")
    ax2.plot(meses, cto_add_cum, label="CAPEX diluído acumulado")
    ax2.set_xlabel("Meses")
    ax2.set_ylabel("Custo (BRL base)")
    ax2.legend()
    st.pyplot(fig2)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 10) Export Excel
# ============================================================
st.markdown('<div class="section-title">10) Exportar Excel</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    resumo = pd.DataFrame({
        "Indicador": [
            "CTO atual (base) mensal",
            "CAPEX total do projeto",
            "CAPEX diluído / mês",
            "CTO novo mensal",
            "Impacto % no CTO",
            "Horizonte (meses)",
            "Taxa desconto anual",
            "VPL do projeto (sem economia)",
            "TIR real anual"
        ],
        "Valor_BRL_base": [
            cto_base_brl,
            capex_total_brl,
            cto_add_mensal_brl,
            cto_novo_brl,
            share_pct,
            horizon,
            taxa_anual/100,
            vpl_proj_brl,
            tir_real_a if tir_real_a is not None else np.nan
        ],
        "Valor_na_moeda": [
            from_brl(cto_base_brl, moeda, fx_rate),
            from_brl(capex_total_brl, moeda, fx_rate),
            from_brl(cto_add_mensal_brl, moeda, fx_rate),
            from_brl(cto_novo_brl, moeda, fx_rate),
            share_pct,
            horizon,
            taxa_anual/100,
            from_brl(vpl_proj_brl, moeda, fx_rate),
            tir_real_a if tir_real_a is not None else np.nan
        ],
        "Moeda": [moeda]*9
    })

    cto_det = pd.DataFrame({
        "Campo": fields,
        "Valor_por_hub_BRL": [detailed_vals_brl[f] for f in fields],
        "Valor_total_BRL": [detailed_vals_brl[f]*total_hubs for f in fields]
    })

    kit_export = kit.copy()
    kit_export["CAPEX_total_brl"] = kit["CAPEX_total_brl"]

    fluxo = pd.DataFrame({
        "Mes": meses,
        "CTO_atual_BRL": cto_atual_series,
        "CTO_novo_BRL": cto_novo_series,
        "CTO_add_BRL": cto_novo_series - cto_atual_series
    })

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        resumo.to_excel(writer, sheet_name="Resumo", index=False)
        cto_det.to_excel(writer, sheet_name="CTO_detalhado", index=False)
        kit_export.to_excel(writer, sheet_name="CAPEX_kit", index=False)
        fluxo.to_excel(writer, sheet_name="Series", index=False)

    buffer.seek(0)
    st.download_button(
        "📥 Baixar Excel",
        data=buffer,
        file_name=f"viabilidade_projeto_shopee_{moeda.lower()}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.markdown('</div>', unsafe_allow_html=True)

st.caption("FINAL ✅ | CTO real + CAPEX adicional diluído + impacto % + BRL/USD + export")
