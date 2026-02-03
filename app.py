import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import base64
from pandas.tseries.offsets import BDay

# =====================
# CONFIGURAÇÃO DA PÁGINA
# =====================
st.set_page_config(
    page_title="Aluguel de Ações — Análise de Mercado",
    layout="wide"
)

# =====================
# HEADER ITAÚ COM LOGO
# =====================
def get_base64_image(path):
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()

logo_base64 = get_base64_image("logos/logo.webp")

st.markdown(f"""
<style>
html, body, [class*="css"] {{
    font-family: 'Segoe UI', sans-serif;
}}

.header-itau {{
    background: linear-gradient(90deg, #f58220 0%, #ff9f4d 100%);
    padding: 25px 30px;
    border-radius: 12px;
    margin-bottom: 30px;
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}

.header-text h1 {{
    margin: 0;
    font-size: 32px;
    font-weight: 700;
}}

.header-text h3 {{
    margin: 5px 0 0 0;
    font-weight: 400;
}}

.header-logo img {{
    height: 55px;
}}
</style>

<div class="header-itau">
    <div class="header-text">
        <h1>Aluguel de Ações — Análise de Mercado</h1>
        <h3>Itaú BBA · Mesa de Aluguel</h3>
    </div>
    <div class="header-logo">
        <img src="data:image/webp;base64,{logo_base64}">
    </div>
</div>
""", unsafe_allow_html=True)

# =====================
# CARREGAMENTO AUTOMÁTICO DOS CSVs
# =====================
PASTA_DADOS = Path("dados")
arquivos_csv = list(PASTA_DADOS.glob("*.csv"))

if not arquivos_csv:
    st.error("Nenhum arquivo CSV encontrado na pasta 'dados'")
    st.stop()

dfs = []
for arq in arquivos_csv:
    temp = pd.read_csv(arq, sep=";", encoding="utf-8-sig", header=1)
    dfs.append(temp)

df = pd.concat(dfs, ignore_index=True)

# =====================
# TRATAMENTO DA BASE
# =====================
# df.columns = (
#     df.columns.astype(str)
#     .str.replace("\ufeff", "", regex=False)
#     .str.strip()
# )

# df["Quantidade"] = (
#     df["Quantidade"]
#     .astype(str)
#     .str.replace(".", "", regex=False)
#     .astype(int)
# )

# Ajusta Quantidade
df["Quantidade"] = (
    df["Quantidade"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .astype(int)
)

# Ajusta Taxa % remuneração  ← ESSENCIAL
df["Taxa % remuneração"] = (
    df["Taxa % remuneração"]
    .astype(str)
    .str.replace("%", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.strip()
)

df["Taxa % remuneração"] = pd.to_numeric(
    df["Taxa % remuneração"],
    errors="coerce"
) / 100

# Remove papel problemático
df = df[df["Código IF"] != "AZUL53"]

# Converte data
df["Data de referência"] = pd.to_datetime(
    df["Data de referência"],
    dayfirst=True,
    errors="coerce"
)

df = df[df["Código IF"] != "AZUL53"]

df["Data de referência"] = pd.to_datetime(
    df["Data de referência"], dayfirst=True, errors="coerce"
)

# =====================
# SIDEBAR
# =====================
st.sidebar.title("📊 Navegação")
tela = st.sidebar.radio(
    "Escolha a visão:",
    ["Mercado", "Papel", "Pool", "Perdas e Ganhos"]
)

# =====================
# FILTRO DE DATA GLOBAL
# =====================
# st.subheader("📅 Período de Análise")

# c1, c2 = st.columns(2)
# data_ini = c1.date_input("Data inicial", df["Data de referência"].min())
# data_fim = c2.date_input("Data final", df["Data de referência"].max())

# df_filtrado = df[
#     (df["Data de referência"] >= pd.to_datetime(data_ini)) &
#     (df["Data de referência"] <= pd.to_datetime(data_fim))
# ]

st.subheader("📅 Período de Análise")

# --- calcula D-1 útil ---
hoje = pd.Timestamp.today().normalize()
d_1_util = hoje - BDay(1)

# garante que está dentro do range do dataframe
data_min = df["Data de referência"].min()
data_max = df["Data de referência"].max()

data_default = min(max(d_1_util, data_min), data_max)

c1, c2 = st.columns(2)

data_ini = c1.date_input(
    "Data inicial",
    value=data_default.date()
)

data_fim = c2.date_input(
    "Data final",
    value=data_default.date()
)

df_filtrado = df[
    (df["Data de referência"] >= pd.to_datetime(data_ini)) &
    (df["Data de referência"] <= pd.to_datetime(data_fim))
]

# =====================
# FUNÇÃO DE DESTAQUE ITAÚ
# =====================
def highlight_itau(row, col):
    if row[col] == "ITAU CV S/A":
        return ["background-color: #f58220; color: white"] * len(row)
    return [""] * len(row)

# =====================
# TELA MERCADO
# =====================
if tela == "Mercado":

    # -------- TOP 7 TOMADORES --------
    st.subheader("📥 Maiores Tomadores (Quantidade)")
    top_tomadores = (
        df_filtrado.groupby("Nome tomador")["Quantidade"]
        .sum().sort_values(ascending=False).head(15).reset_index()
    )

    top_tomadores.insert(
    0,
    "Posição",
    [f"{i}º" for i in range(1, len(top_tomadores) + 1)]
    )

    st.dataframe(
        top_tomadores.style
        .format({"Quantidade": "{:,.0f}".format})
        .apply(lambda r: highlight_itau(r, "Nome tomador"), axis=1),
        use_container_width=True,
        hide_index=True
    )

    # -------- TOP 7 DOADORES --------
    st.subheader("📤 Maiores Doadores (Quantidade)")
    top_doadores = (
        df_filtrado.groupby("Nome doador")["Quantidade"]
        .sum().sort_values(ascending=False).head(15).reset_index()
    )

    top_doadores.insert(
    0,
    "Posição",
    [f"{i}º" for i in range(1, len(top_doadores) + 1)]
    )

    st.dataframe(
        top_doadores.style
        .format({"Quantidade": "{:,.0f}".format})
        .apply(lambda r: highlight_itau(r, "Nome doador"), axis=1),
        use_container_width=True,
        hide_index=True
    )

    # -------- GRÁFICO PAPÉIS MAIS NEGOCIADOS --------
    st.subheader("📊 Papéis Mais Negociados (Quantidade)")
    top_papeis = (
        df_filtrado.groupby("Código IF")["Quantidade"]
        .sum().sort_values(ascending=False).head(15).reset_index()
    )
    top_papeis["rank"] = range(len(top_papeis))

    fig_qtd = px.bar(
        top_papeis,
        x="Quantidade",
        y="Código IF",
        orientation="h",
        color="rank",
        color_continuous_scale=["#f58220", "#ffe6cc"],
        text="Quantidade"
    )
    fig_qtd.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_qtd.update_layout(
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_qtd, use_container_width=True)

# -------- GRÁFICO FINANCEIRO --------

    st.subheader("📊 Papéis que mais rendem dinheiro")
    # Carrega tabela de preços
    df_preco = pd.read_excel("preços.xlsx")

    df_filtrado["Taxa % remuneração"] = (
    df_filtrado["Taxa % remuneração"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
        
)

    # Base agregada por papel (Quantidade + Taxa média)
    base_papel = (
        df_filtrado
            .groupby("Código IF")
            .agg({
                "Quantidade": "sum",
                "Taxa % remuneração": "mean"
            })
            .reset_index()
    )


# =====================
# AJUSTE DA TAXA % REMUNERAÇÃO (OBRIGATÓRIO)
# =====================
    df["Taxa % remuneração"] = (
        df["Taxa % remuneração"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

    df["Taxa % remuneração"] = pd.to_numeric(
        df["Taxa % remuneração"],
        errors="coerce"
    ) / 100


    # Junta com preços
    df_valor = base_papel.merge(
        df_preco,
        on="Código IF",
        how="inner"
    )

    # Cálculo financeiro CORRETO
    df_valor["Financeiro"] = (
        df_valor["Quantidade"]
        * df_valor["Preço"]
        * df_valor["Taxa % remuneração"]
    )

    top_fin = df_valor.sort_values("Financeiro", ascending=False).head(20)
    top_fin["rank"] = range(len(top_fin))

    fig_fin = px.bar(
        top_fin,
        x="Financeiro",
        y="Código IF",
        orientation="h",
        color="rank",
        color_continuous_scale=["#f58220", "#ffe6cc"],
        text="Financeiro"
    )
    fig_fin.update_traces(texttemplate="R$ %{text:,.0f}", textposition="outside")
    fig_fin.update_layout(
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=450  # 🔑 ISSO CRIA O SCROLL

    )

    fig_fin.update_layout(
        yaxis=dict(
            autorange="reversed",
            automargin=True
        ),
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"   # gráfico alto (importante!)
    )
    
    st.plotly_chart(fig_fin, use_container_width=True)

    # -------- TOP 3 PAPÉIS DETALHADOS --------
    st.subheader("🏆 Detalhamento dos Papéis que Mais Geraram Dinheiro")
    top3_papeis = top_fin["Código IF"].head(5).tolist()

    for papel in top3_papeis:
        st.markdown(f"### 📄 Papel: **{papel}**")
        base = df_filtrado[df_filtrado["Código IF"] == papel]
        total = base["Quantidade"].sum()

        col1, col2 = st.columns(2)

            # 🔑 DEFINE O PREÇO DO PAPEL AQUI
        preco_papel = df_preco.loc[
            df_preco["Código IF"] == papel, "Preço"
        ].iloc[0]

        col1, col2 = st.columns(2)
 
        with col1:
            st.markdown("**🏦 Top 5 Doadores**")

            top_doadores = (
                base
                    .groupby("Nome doador", as_index=False)
                    .agg({
                        "Quantidade": "sum",
                        "Taxa % remuneração": "mean"
                    })
            )


            top_doadores["Financeiro"] = (
                top_doadores["Quantidade"]
                * preco_papel
                * top_doadores["Taxa % remuneração"]
            )

            top_doadores = (
                top_doadores
                .sort_values("Financeiro", ascending=False)
                .head(5)
                .reset_index(drop=True)
            )

                          # ranking
            top_doadores.insert(
                0,
                "Posição",
                [f"{i}º" for i in range(1, len(top_doadores) + 1)]
            )

            st.dataframe(
                top_doadores
                    .sort_values("Quantidade", ascending=False)
                    .head(5)[[
                        "Posição",
                        "Nome doador",
                        "Quantidade",
                        "Financeiro"
                    ]]
                    .style.format({
                        "Quantidade": "{:,.0f}",
                        "Financeiro": "R$ {:,.2f}"
                    }),
                use_container_width=True,
                hide_index=True
            )


        with col2:
            st.markdown("**📥 Top 5 Tomadores**")

            top_tomadores = (
                base
                    .groupby("Nome tomador", as_index=False)
                    .agg({
                        "Quantidade": "sum",
                        "Taxa % remuneração": "mean"
                    })
            )

            top_tomadores["Financeiro"] = (
                top_tomadores["Quantidade"]
                * preco_papel
                * top_tomadores["Taxa % remuneração"]
            )

            top_tomadores = (
                top_tomadores
                .sort_values("Financeiro", ascending=False)
                .head(5)
                .reset_index(drop=True)
            )

            top_tomadores.insert(
                0,
                "Posição",
                [f"{i}º" for i in range(1, len(top_tomadores) + 1)]
            )

            st.dataframe(
                top_tomadores
                    .sort_values("Quantidade", ascending=False)
                    .head(5)[[
                        "Posição",
                        "Nome tomador",
                        "Quantidade",
                        "Financeiro"
                    ]]
                    .style.format({
                        "Quantidade": "{:,.0f}",
                        "Financeiro": "R$ {:,.2f}"
                    }),
                use_container_width=True,
                hide_index=True
            )


        qtd_itau_d = base[base["Nome doador"] == "ITAU CV S/A"]["Quantidade"].sum()
        qtd_itau_t = base[base["Nome tomador"] == "ITAU CV S/A"]["Quantidade"].sum()

        perc_d = (qtd_itau_d / total) * 100 if total else 0
        perc_t = (qtd_itau_t / total) * 100 if total else 0

        txt_d = "_Não representativo (<5%)_" if perc_d < 5 else f"**{perc_d:.1f}%**"
        txt_t = "_Não representativo (<5%)_" if perc_t < 5 else f"**{perc_t:.1f}%**"

        st.markdown(
            f"""
            **🔎 Representatividade do Itaú**
            - **Doador**: {txt_d}
            - **Tomador**: {txt_t}
            """
        )

    st.divider()

# =====================
# TELA PAPEL
# =====================
if tela == "Papel":

    st.title("📄 Análise por Papel")

    # =====================
    # SELEÇÃO DO PAPEL
    # =====================
    lista_papeis = sorted(
        df_filtrado["Código IF"]
        .dropna()
        .unique()
        .tolist()
    )

    papel = st.selectbox(
        "Digite ou selecione o Código IF",
        lista_papeis,
        index=None,
        placeholder="Ex: VALE3"
    )

    if papel is None:
        st.info("Selecione um papel para iniciar a análise.")
        st.stop()



    # =====================
    # BASE DO PAPEL
    # =====================
    df_papel = df_filtrado[df_filtrado["Código IF"] == papel]

    # =====================
    # KPIs DO PAPEL
    # =====================
    total_negocios = df_papel['Quantidade'].sum()

    # =====================
    taxa_media = df_papel["Taxa % remuneração"].mean() * 100

    col1, col2 = st.columns(2)

    col1.metric("Quantidade de Negócios", f"{total_negocios:,}")
    col2.metric("Taxa Média Calculada (%)", f"{taxa_media:.2f}%")

    st.divider()

    # =====================
    # TOP 6 TOMADORES
    # =====================
    st.subheader("📥 Top 8 Tomadores (Quantidade)")

    top6_tomadores = (
        df_papel.groupby("Nome tomador")["Quantidade"]
        .sum()
        .sort_values(ascending=False)
        .head(8)
        .reset_index()
    )

    top6_tomadores.insert(
        0,
        "Posição",
        [f"{i}º" for i in range(1, len(top6_tomadores) + 1)]
    )

    st.dataframe(
        top6_tomadores
        .style
        .format({"Quantidade": "{:,.0f}".format})
        .apply(lambda r: highlight_itau(r, "Nome tomador"), axis=1),
        use_container_width=True,
        hide_index=True
    )

    # =====================
    # TOP 6 DOADORES
    # =====================
    st.subheader("📤 Top 8 Doadores (Quantidade)")

    top6_doadores = (
        df_papel.groupby("Nome doador")["Quantidade"]
        .sum()
        .sort_values(ascending=False)
        .head(8)
        .reset_index()
    )

    top6_doadores.insert(
        0,
        "Posição",
        [f"{i}º" for i in range(1, len(top6_doadores) + 1)]
    )

    st.dataframe(
        top6_doadores
        .style
        .format({"Quantidade": "{:,.0f}".format})
        .apply(lambda r: highlight_itau(r, "Nome doador"), axis=1),
        use_container_width=True,
        hide_index=True
    )

# =====================
# MATRIZ DOADOR x TOMADOR (PIVOT)
# =====================
    st.subheader("📊 Matriz Doador × Tomador (Quantidade de Ações)")

    pivot_doador_tomador = pd.pivot_table(
        df_papel,                 # já vem filtrado por papel + data
        values="Quantidade",
        index="Código",           # Código DOADOR (coluna J)
        columns="Código.1",       # Código TOMADOR (coluna L)
        aggfunc="sum",
        fill_value=0
    )

    st.dataframe(
        pivot_doador_tomador.style.format("{:,.0f}"),
        use_container_width=True
    )

    st.subheader("📊 Tabela Dinâmica — Taxa Média (%)")

    # -------------------------------------------------
    # BASE
    # -------------------------------------------------
    df_base = df_papel.copy()

    # 🔑 GARANTE QUE CÓDIGO É STRING
    df_base["Código"] = df_base["Código"].astype(str)
    df_base["Código.1"] = df_base["Código.1"].astype(str)

    # -------------------------------------------------
    # TAXA COMO TEXTO PERCENTUAL (IGUAL EXCEL)
    # -------------------------------------------------
    df_base["Taxa % remuneração"] = (
        df_base["Taxa % remuneração"]
            .mul(100)
            .round(2)
            .astype(str)
            .str.replace(".", ",", regex=False)
            + "%"
    )

    # -------------------------------------------------
    # PIVOT IGUAL AO EXCEL
    # -------------------------------------------------
    pivot_excel = pd.pivot_table(
        df_base,
        values="Quantidade",
        index=["Código", "Taxa % remuneração"],
        columns="Código.1",
        aggfunc="sum",
        margins=True,
        margins_name="Grand Total"
    )

    # -------------------------------------------------
    # AJUSTA NOMES DOS EIXOS (MULTIINDEX CORRETO)
    # -------------------------------------------------
    pivot_excel = pivot_excel.rename_axis(
        index=["Row Labels", ""],
        columns="Column Labels"
    )

    # -------------------------------------------------
    # FORMATAÇÃO NUMÉRICA
    # -------------------------------------------------
    pivot_excel_style = (
        pivot_excel
            .style
            .format("{:,.0f}", na_rep="")
    )

    # -------------------------------------------------
    # EXIBIÇÃO
    # -------------------------------------------------
    st.dataframe(
        pivot_excel_style,
        use_container_width=True,
        height=520
    )


# =====================
# RODAPÉ
# =====================
st.markdown("""
<style>
.footer-itau {
    margin-top: 60px;
    padding-top: 20px;
    border-top: 1px solid #e6e6e6;
    text-align: center;
}
.footer-itau .title {
    font-size: 14px;
    font-weight: 600;
}
.footer-itau .names {
    font-size: 13px;
    color: #666;
}
</style>

<div class="footer-itau">
    <div class="title">Time de Aluguel</div>
    <div class="names">
        Carolina Casseb · Gabriela Albuquerque · Henrique Lira
    </div>
</div>
""", unsafe_allow_html=True)
