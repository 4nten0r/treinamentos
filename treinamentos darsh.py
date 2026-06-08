import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COR_FUNDO = "#002020"
COR_SIDEBAR = "#002040"
COR_CARD = "#004040"
COR_SECUNDARIA = "#208080"
COR_PRIMARIA = "#2CCBC0"
COR_TEXTO = "#EAEAEA"
COR_TEXTO_SEC = "#80A0A0"
COR_META = "#D4B44A"
COR_ALERTA = "#FF4D57"

COLOR_SCALE = [
    [0, "#002040"],
    [0.25, "#004040"],
    [0.5, "#208080"],
    [0.75, "#2CCBC0"],
    [1, "#D4B44A"]
]

st.set_page_config(
    page_title="Dashboard Corporativo de Treinamentos",
    page_icon="📚",
    layout="wide"
)

st.markdown(f"""
<style>
.stApp {{background-color:{COR_FUNDO}; color:{COR_TEXTO};}}
section[data-testid="stSidebar"] {{background-color:{COR_SIDEBAR};}}
[data-testid="metric-container"] {{
 background-color:{COR_CARD};
 border:1px solid {COR_SECUNDARIA};
 border-radius:16px;
 padding:20px;
}}
h1,h2,h3,h4 {{color:{COR_PRIMARIA};}}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_excel(arq):
    participantes = pd.read_excel(arq, sheet_name="participantes")
    motoristas = pd.read_excel(arq, sheet_name="motoristas")

    participantes.columns = participantes.columns.str.lower().str.strip()
    motoristas.columns = motoristas.columns.str.lower().str.strip()

    participantes["data"] = pd.to_datetime(participantes["data"])

    return participantes, motoristas

st.sidebar.title("⚙ Configurações")

arquivo = st.sidebar.file_uploader("Enviar Excel", type=["xlsx"])

if arquivo is None:
    st.info("Faça upload do arquivo Excel para iniciar.")
    st.stop()

df, base = carregar_excel(arquivo)

st.sidebar.header("Filtros")

filial = st.sidebar.selectbox(
    "Filial",
    ["Todas"] + sorted(df["filial"].dropna().unique())
)

if filial != "Todas":
    df = df[df["filial"] == filial]
    base = base[base["filial"] == filial]

treinamentos = st.sidebar.multiselect(
    "Treinamentos",
    sorted(df["treinamento"].dropna().unique())
)

if treinamentos:
    df = df[df["treinamento"].isin(treinamentos)]

periodo = st.sidebar.date_input(
    "Período",
    [df["data"].min(), df["data"].max()]
)

if len(periodo) == 2:
    inicio, fim = periodo
    df = df[
        (df["data"] >= pd.to_datetime(inicio))
        &
        (df["data"] <= pd.to_datetime(fim))
    ]

base_total = base["nome"].nunique()
treinados = df["nome"].nunique()
nao_treinados = max(base_total - treinados, 0)
cobertura = round((treinados/base_total)*100,2) if base_total else 0

st.title("📚 Dashboard Corporativo de Treinamentos")

c1,c2,c3,c4 = st.columns(4)
c1.metric("Treinados", treinados)
c2.metric("Não Treinados", nao_treinados)
c3.metric("Cobertura", f"{cobertura}%")
c4.metric("Base Total", base_total)

tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "📊 Visão Geral","🏢 Filiais","📚 Treinamentos",
    "👤 Participantes","📈 Análises"
])

with tab1:
    col1,col2 = st.columns([2,1])

    with col1:
        cont = df["treinamento"].value_counts().reset_index()
        cont.columns = ["Treinamento","Quantidade"]

        fig = px.bar(
            cont,
            x="Treinamento",
            y="Quantidade",
            color="Quantidade",
            color_continuous_scale=COLOR_SCALE
        )
        fig.update_layout(
            paper_bgcolor=COR_CARD,
            plot_bgcolor=COR_CARD,
            font_color=COR_TEXTO
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=cobertura,
            number={"suffix":"%"},
            title={"text":"Cobertura"},
            gauge={
                "axis":{"range":[0,100]},
                "bar":{"color":COR_PRIMARIA}
            }
        ))
        gauge.update_layout(
            paper_bgcolor=COR_CARD,
            font_color=COR_TEXTO
        )
        st.plotly_chart(gauge, use_container_width=True)

with tab2:
    cobertura_filial = (
        df.groupby("filial")["nome"]
        .nunique()
        .reset_index()
    )

    fig = px.bar(
        cobertura_filial,
        x="filial",
        y="nome",
        color="nome",
        color_continuous_scale=COLOR_SCALE
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    heat = pd.pivot_table(
        df,
        index="filial",
        columns="treinamento",
        values="nome",
        aggfunc="count",
        fill_value=0
    )

    fig = px.imshow(
        heat,
        text_auto=True,
        color_continuous_scale=COLOR_SCALE
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    filial_drill = st.selectbox(
        "Filial",
        sorted(df["filial"].dropna().unique())
    )

    d1 = df[df["filial"] == filial_drill]

    treinamento_drill = st.selectbox(
        "Treinamento",
        sorted(d1["treinamento"].dropna().unique())
    )

    d2 = d1[d1["treinamento"] == treinamento_drill]

    st.dataframe(d2, use_container_width=True)

with tab5:
    evo = (
        df.groupby(df["data"].dt.date)
        .size()
        .cumsum()
        .reset_index(name="Acumulado")
    )

    fig = px.line(
        evo,
        x="data",
        y="Acumulado",
        markers=True
    )

    st.plotly_chart(fig, use_container_width=True)

csv = df.to_csv(
    index=False,
    sep=";"
).encode("utf-8-sig")

st.download_button(
    "⬇ Exportar CSV",
    csv,
    "treinamentos.csv",
    "text/csv"
)
