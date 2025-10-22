import streamlit as st
import pandas as pd
import os
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap
import plotly.express as px

st.set_page_config(page_title="Mapa de Calor - Indicadores", layout="wide")
st.title("🔥 Mapa de Calor e Indicadores por Faixa Etária")

# =============================
# CAMINHOS
# =============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
excel_path = os.path.join(DATA_DIR, "MapaCalor.xlsx")
coords_path = os.path.join(DATA_DIR, "coordenadas_prontas.csv")

# =============================
# CHECAGENS
# =============================
erros = []
if not os.path.exists(excel_path):
    erros.append(f"❌ Não achei {excel_path}")
if not os.path.exists(coords_path):
    erros.append(f"❌ Não achei {coords_path}")
if erros:
    st.error(" | ".join(erros))
    st.stop()

# =============================
# LEITURA E PADRONIZAÇÃO
# =============================
df = pd.read_excel(excel_path)
coords = pd.read_csv(coords_path)

df.columns = df.columns.str.strip().str.upper()
coords.columns = coords.columns.str.strip().str.upper()

df = df.rename(columns={
    "CIDADE": "Cidade",
    "IDADE": "Idade",
    "QUANTIDADE DE INDICACOES": "Quantidade",
    "QUANTIDADE_DE_INDICACOES": "Quantidade"
})
coords = coords.rename(columns={
    "CIDADE": "Cidade",
    "LAT": "lat",
    "LON": "lon"
})

# =============================
# FAIXAS ETÁRIAS
# =============================
df["Idade"] = pd.to_numeric(df["Idade"], errors="coerce")

def faixa_etaria(idade):
    if pd.isna(idade):
        return "Sem informação"
    elif idade <= 18:
        return "Até 18"
    elif idade <= 30:
        return "19 a 30"
    elif idade <= 50:
        return "31 a 50"
    elif idade <= 60:
        return "51 a 60"
    elif idade <= 80:
        return "61 a 80"
    else:
        return "Acima de 80"

df["FaixaEtaria"] = df["Idade"].apply(faixa_etaria)

# =============================
# FILTRO
# =============================
faixas = ["Todas"] + sorted(df["FaixaEtaria"].unique())
faixa_sel = st.sidebar.selectbox("👤 Selecione uma faixa etária:", faixas)

if faixa_sel != "Todas":
    df_filtrado = df[df["FaixaEtaria"] == faixa_sel]
else:
    df_filtrado = df.copy()

# =============================
# AGREGAÇÃO
# =============================
df_agg = df_filtrado.groupby("Cidade", as_index=False)["Quantidade"].sum()

# =============================
# MERGE E VALIDAÇÕES
# =============================
dfm = df_agg.merge(coords, on="Cidade", how="left")
faltando_coords = dfm["lat"].isna().sum()
if faltando_coords > 0:
    st.warning(f"⚠️ {faltando_coords} cidades não têm coordenadas e foram ignoradas no mapa.")
dfm = dfm.dropna(subset=["lat", "lon"])

# =============================
# MAPA DE CALOR
# =============================
m = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)
HeatMap(dfm[["lat", "lon", "Quantidade"]].values.tolist(), radius=18, blur=15).add_to(m)

# =============================
# LEGENDA
# =============================
max_qtd = dfm["Quantidade"].max() if len(dfm) > 0 else 0
legend_html = f"""
<div style="
    position: fixed; 
    bottom: 50px; left: 50px; width: 240px; height: 140px; 
    background-color: rgba(255, 255, 255, 0.85);
    border-radius: 12px; padding: 10px; font-size: 14px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    z-index: 9999;">
    <b>🟢 Legenda - Intensidade</b><br>
    Verde = Baixa (≤ {max_qtd * 0.25:.0f})<br>
    Amarelo = Média ({max_qtd * 0.25:.0f}–{max_qtd * 0.5:.0f})<br>
    Laranja = Alta ({max_qtd * 0.5:.0f}–{max_qtd * 0.75:.0f})<br>
    Vermelho = Muito Alta (> {max_qtd * 0.75:.0f})
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# =============================
# EXIBE MAPA
# =============================
st.subheader(f"Faixa etária selecionada: **{faixa_sel}**")
st_folium(m, width=1200, height=600)

# =============================
# GRÁFICOS COMPLEMENTARES
# =============================
st.markdown("---")
st.subheader("📊 Indicadores complementares")

# --- Gráfico 1: Indicações por Faixa Etária (base total)
faixa_chart = df.groupby("FaixaEtaria", as_index=False)["Quantidade"].sum().sort_values("FaixaEtaria")
fig1 = px.bar(
    faixa_chart,
    x="FaixaEtaria",
    y="Quantidade",
    color="FaixaEtaria",
    title="Quantidade de Indicações por Faixa Etária",
    text_auto=True,
)
st.plotly_chart(fig1, use_container_width=True)

# --- Gráfico 2: Indicações por Cidade (filtrado)
top_cidades = df_filtrado.groupby("Cidade", as_index=False)["Quantidade"].sum().sort_values("Quantidade", ascending=False).head(15)
fig2 = px.bar(
    top_cidades,
    x="Cidade",
    y="Quantidade",
    color="Cidade",
    title=f"Top 15 Cidades com Mais Indicações ({faixa_sel})",
    text_auto=True,
)
st.plotly_chart(fig2, use_container_width=True)

# =============================
# TABELA FINAL
# =============================
with st.expander("📋 Ver dados agregados"):
    st.dataframe(dfm)
