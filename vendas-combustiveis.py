import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# FUNÇÃO AUXILIAR DE FORMATAÇÃO (PADRÃO BRASILEIRO)
# =========================================================
def fmt_br(valor):
    """Formata números no padrão brasileiro: 1.900,02"""
    if pd.isna(valor):
        return ""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# Configuração global para formatar números nos gráficos Plotly no padrão BR
FORMATO_NUMERO_BR = dict(separators=",.")

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Dashboard - Vendas de Combustíveis", layout="wide"
)

CAMINHO_ARQUIVO = "vendas-combustiveis-m3-1990-2025.csv"


# =========================================================
# CARREGAMENTO E TRATAMENTO DOS DADOS COM CACHING
# =========================================================
@st.cache_data
def carregar_e_tratar_dados(caminho):
    df = pd.read_csv(caminho, sep=None, engine="python")

    # Limpeza do nome das colunas
    df.columns = df.columns.str.replace("\ufeff", "").str.strip()

    colunas_necessarias = [
        "ANO",
        "MÊS",
        "GRANDE REGIÃO",
        "UNIDADE DA FEDERAÇÃO",
        "PRODUTO",
        "VENDAS",
    ]
    for col in colunas_necessarias:
        if col not in df.columns:
            raise KeyError(
                f"A coluna '{col}' não foi encontrada na base de dados."
            )

    # Tratamento da coluna de vendas
    df["VENDAS"] = df["VENDAS"].astype(str).str.replace(",", ".").str.strip()
    df["VENDAS"] = pd.to_numeric(df["VENDAS"], errors="coerce")

    return df


try:
    df = carregar_e_tratar_dados(CAMINHO_ARQUIVO)

    # =========================================================
    # BARRA LATERAL (SIDEBAR): INFORMAÇÕES DO ARQUIVO BASE
    # =========================================================
    st.sidebar.header("📄 Diagnóstico do Arquivo Base")
    st.sidebar.info(f"**Arquivo analisado:** `{CAMINHO_ARQUIVO}`")

    total_linhas = len(df)
    total_colunas = len(df.columns)
    total_nulos = df.isnull().sum().sum()
    total_duplicados = df.duplicated().sum()
    memoria_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

    st.sidebar.metric("Total de Registros", f"{fmt_br(total_linhas)[:-3]}")
    st.sidebar.metric("Total de Colunas", f"{total_colunas}")
    st.sidebar.metric("Valores Nulos", f"{total_nulos}")
    st.sidebar.metric("Linhas Duplicadas", f"{total_duplicados}")
    st.sidebar.caption(f"Tamanho na Memória: {fmt_br(memoria_mb)} MB")

    with st.sidebar.expander("📋 Detalhes das Colunas e Tipos"):
        df_info = pd.DataFrame({
            "Coluna": df.columns,
            "Tipo": [str(dtype) for dtype in df.dtypes],
            "Nulos": [df[col].isnull().sum() for col in df.columns],
        })
        st.sidebar.dataframe(
            df_info, use_container_width=True, hide_index=True
        )

    # =========================================================
    # CABEÇALHO PRINCIPAL DA APLICAÇÃO
    # =========================================================
    st.title("⛽ Dashboard de Vendas de Combustíveis no Brasil")
    st.markdown("""
    **Tema:** Economia e Transporte (Consumo de Combustíveis)  
    **Fonte dos Dados:** Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP) / dados.gov.br  
    ---
    **Feito por:** Arthur Sartori Cavalcanti  
    **Orientado por:** Felipe Garbin  
    """)

    st.subheader("📖 Sobre a Aplicação")
    st.markdown("""
    Esta aplicação interativa foi desenvolvida para analisar e explorar a distribuição histórica das vendas de combustíveis nas diferentes regiões e estados do Brasil.

    **Como navegar no Dashboard:**
    1. **Filtros e Seleções:** Ajuste o período de anos, selecione uma região e escolha os estados desejados no painel abaixo.
    2. **Visualização:** Alterne entre a **Visão Geral** ou escolha um **Combustível Específico** na caixa de seleção abaixo.
    3. **Barra Lateral:** Consulte a auditoria técnica e o diagnóstico da base de dados carregada.
    """)

    st.markdown("---")

    # =========================================================
    # PAINEL PRINCIPAL DE CONTROLE E FILTROS
    # =========================================================
    st.subheader("🎛️ Navegação e Filtros de Pesquisa")

    col_nav, col_ano = st.columns([2, 2])

    produtos_unicos = sorted(list(df["PRODUTO"].dropna().unique()))
    opcoes_navegacao = ["🌐 Visão Geral (Todos os Combustíveis)"] + [
        f"⛽ {prod}" for prod in produtos_unicos
    ]

    with col_nav:
        pagina_selecionada = st.selectbox(
            "📌 Selecione a Visualização:", opcoes_navegacao
        )

    with col_ano:
        ano_min = int(df["ANO"].min())
        ano_max = int(df["ANO"].max())
        intervalo_anos = st.slider(
            "📅 Período (Anos):",
            min_value=ano_min,
            max_value=ano_max,
            value=(ano_min, ano_max),
        )

    col_regiao, col_estados = st.columns([2, 2])

    regioes_unicas = sorted(list(df["GRANDE REGIÃO"].dropna().unique()))
    opcoes_regiao = ["Todas as Regiões"] + regioes_unicas

    with col_regiao:
        regiao_escolhida = st.selectbox("🗺️ Selecione a Região:", opcoes_regiao)

    if regiao_escolhida == "Todas as Regiões":
        estados_filtrados = sorted(
            list(df["UNIDADE DA FEDERAÇÃO"].dropna().unique())
        )
    else:
        estados_filtrados = sorted(
            list(
                df[df["GRANDE REGIÃO"] == regiao_escolhida][
                    "UNIDADE DA FEDERAÇÃO"
                ]
                .dropna()
                .unique()
            )
        )

    with col_estados:
        estados_selecionados = st.multiselect(
            f"🏛️ Estados pertencentes ({regiao_escolhida}):",
            options=estados_filtrados,
            default=estados_filtrados,
        )

    if not estados_selecionados:
        st.warning(
            "⚠️ Selecione pelo menos um estado no filtro acima para carregar os"
            " dados."
        )
        st.stop()

    # DataFrame Filtrado
    if regiao_escolhida == "Todas as Regiões":
        df_filtrado = df[
            (df["ANO"] >= intervalo_anos[0])
            & (df["ANO"] <= intervalo_anos[1])
            & (df["UNIDADE DA FEDERAÇÃO"].isin(estados_selecionados))
        ]
    else:
        df_filtrado = df[
            (df["ANO"] >= intervalo_anos[0])
            & (df["ANO"] <= intervalo_anos[1])
            & (df["GRANDE REGIÃO"] == regiao_escolhida)
            & (df["UNIDADE DA FEDERAÇÃO"].isin(estados_selecionados))
        ]

    st.markdown("---")

    # =========================================================
    # VISUALIZAÇÃO 1: VISÃO GERAL (TODOS OS COMBUSTÍVEIS)
    # =========================================================
    if pagina_selecionada == "🌐 Visão Geral (Todos os Combustíveis)":
        st.header("📊 Visão Geral do Mercado Nacional")

        df_tabela_geral = (
            df_filtrado.groupby("PRODUTO", as_index=False)
            .agg(
                Volume_Total_m3=("VENDAS", "sum"),
                Media_Mensal_m3=("VENDAS", "mean"),
                Registros=("VENDAS", "count"),
            )
            .sort_values(by="Volume_Total_m3", ascending=False)
        )

        total_geral = df_tabela_geral["Volume_Total_m3"].sum()
        df_tabela_geral["Participacao_%"] = (
            df_tabela_geral["Volume_Total_m3"] / total_geral * 100
        ).round(2)

        tabela_formatada = df_tabela_geral.copy()
        tabela_formatada["Volume_Total_m3"] = tabela_formatada[
            "Volume_Total_m3"
        ].apply(fmt_br)
        tabela_formatada["Media_Mensal_m3"] = tabela_formatada[
            "Media_Mensal_m3"
        ].apply(fmt_br)
        tabela_formatada["Participacao_%"] = tabela_formatada[
            "Participacao_%"
        ].apply(lambda x: f"{fmt_br(x)}%")

        st.dataframe(tabela_formatada, use_container_width=True)
        st.markdown("---")

        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Quantidade Total de Registros",
            f"{fmt_br(df_filtrado.shape[0])[:-3]}",
        )
        c2.metric("Volume Total Vendido", f"{fmt_br(total_geral)} m³")
        c3.metric(
            "Média por Registro", f"{fmt_br(df_filtrado['VENDAS'].mean())} m³"
        )

        st.markdown("---")

        # Gráfico 1: Volume Total por Produto
        st.subheader("1. Volume Total Vendido por Tipo de Produto")
        fig_barras_geral = px.bar(
            df_tabela_geral,
            x="PRODUTO",
            y="Volume_Total_m3",
            labels={
                "PRODUTO": "Combustível",
                "Volume_Total_m3": "Volume Vendido (m³)",
            },
            title="Volume Acumulado de Vendas por Categoria (m³)",
            color="Volume_Total_m3",
            color_continuous_scale="Turbo",
            hover_data={"Volume_Total_m3": ":,.2f"},
        )
        fig_barras_geral.update_layout(
            yaxis_tickformat=",.2f", coloraxis_showscale=True
        )
        fig_barras_geral.update_layout(FORMATO_NUMERO_BR)
        st.plotly_chart(fig_barras_geral, use_container_width=True)
        st.info(
            "💡 **O que este gráfico mostra:** Apresenta o volume acumulado em"
            " metros cúbicos (m³) vendido de cada combustível no período"
            " selecionado.\n\n📌 **Observações:** O uso do degradê contínuo"
            " destaca a diferença de escala entre as categorias, transicionando"
            " suavemente das cores mais frias/escuras (menor volume) para cores"
            " quentes/vivas (maior volume)."
        )

        st.markdown("---")

        # Gráfico 2: Evolução Histórica
        st.subheader("2. Evolução Histórica de Vendas por Ano e Combustível")
        df_linha_geral = df_filtrado.groupby(["ANO", "PRODUTO"], as_index=False)[
            "VENDAS"
        ].sum()
        fig_linha_geral = px.line(
            df_linha_geral,
            x="ANO",
            y="VENDAS",
            color="PRODUTO",
            markers=True,
            labels={
                "ANO": "Ano",
                "VENDAS": "Volume Vendido (m³)",
                "PRODUTO": "Tipo de Combustível",
            },
            title="Evolução Temporal do Volume Vendido por Tipo de Combustível (m³)",
            hover_data={"VENDAS": ":,.2f"},
        )
        fig_linha_geral.update_layout(yaxis_tickformat=",.2f")
        fig_linha_geral.update_layout(FORMATO_NUMERO_BR)
        st.plotly_chart(fig_linha_geral, use_container_width=True)
        st.info(
            "💡 **O que este gráfico mostra:** O gráfico mostra a linha do"
            " tempo com a quantidade de combustível vendida por ano no país"
            " para cada categoria.\n\n📌 **Observações:** Os principais"
            " resultados observados são: uma tendência geral de crescimento"
            " nas vendas ao longo dos anos. O Óleo Diesel e a Gasolina C"
            " mantiveram-se no topo da série histórica durante todo o período"
            " registrado."
        )

        st.markdown("---")

        # Gráfico 3: Distribuição Regional/Estadual
        st.subheader("3. Distribuição Geral de Vendas")
        if regiao_escolhida == "Todas as Regiões":
            df_regiao_geral = (
                df_filtrado.groupby("GRANDE REGIÃO", as_index=False)["VENDAS"]
                .sum()
                .sort_values(by="VENDAS", ascending=False)
            )
            fig_rosca_geral = px.pie(
                df_regiao_geral,
                names="GRANDE REGIÃO",
                values="VENDAS",
                title="Participação Percentual por Grande Região",
                hole=0.4,
                hover_data={"VENDAS": ":,.2f"},
            )
        else:
            df_uf_geral = (
                df_filtrado.groupby("UNIDADE DA FEDERAÇÃO", as_index=False)[
                    "VENDAS"
                ]
                .sum()
                .sort_values(by="VENDAS", ascending=False)
            )
            fig_rosca_geral = px.pie(
                df_uf_geral,
                names="UNIDADE DA FEDERAÇÃO",
                values="VENDAS",
                title=(
                    f"Participação Percentual dos Estados da Região"
                    f" {regiao_escolhida}"
                ),
                hole=0.4,
                hover_data={"VENDAS": ":,.2f"},
            )
        fig_rosca_geral.update_layout(FORMATO_NUMERO_BR)
        st.plotly_chart(fig_rosca_geral, use_container_width=True)
        st.info(
            "💡 **O que este gráfico mostra:** Exibe a proporção percentual do"
            " volume vendido dividido por Região ou Estado.\n\n📌"
            " **Observações:** Destaca a concentração do consumo nacional em"
            " determinadas regiões socioeconômicas (ex: Sudeste)."
        )

    # =========================================================
    # VISUALIZAÇÃO 2: ANÁLISES INDIVIDUAIS POR COMBUSTÍVEL
    # =========================================================
    else:
        prod = pagina_selecionada.replace("⛽ ", "")
        df_prod = df_filtrado[df_filtrado["PRODUTO"] == prod]

        if df_prod.empty:
            st.info(
                "Nenhum registro encontrado para este combustível com os"
                " filtros selecionados."
            )
        else:
            vol_total_prod = df_prod["VENDAS"].sum()
            vol_med_prod = df_prod["VENDAS"].mean()

            # =========================================================
            # CASO 1: APENAS 1 ESTADO SELECIONADO
            # =========================================================
            if len(estados_selecionados) == 1:
                uf_unica = estados_selecionados[0]
                st.header(
                    f"⛽ Análise Específica de {prod} — Estado: {uf_unica}"
                )

                m1, m2, m3 = st.columns(3)
                m1.metric(
                    "Volume Acumulado no Estado", f"{fmt_br(vol_total_prod)} m³"
                )
                m2.metric(
                    "Média Mensal do Estado", f"{fmt_br(vol_med_prod)} m³"
                )
                ano_maior = (
                    df_prod.groupby("ANO")["VENDAS"].sum().idxmax()
                    if not df_prod.empty
                    else "-"
                )
                m3.metric("Ano de Maior Venda", ano_maior)

                st.markdown("---")

                # Gráfico 1: Vendas Anuais
                st.subheader(f"1. Volume Anual de {prod} em {uf_unica}")
                df_ano_uf = (
                    df_prod.groupby("ANO", as_index=False)["VENDAS"]
                    .sum()
                    .sort_values(by="ANO")
                )
                fig_bar_ano = px.bar(
                    df_ano_uf,
                    x="ANO",
                    y="VENDAS",
                    color="VENDAS",
                    labels={"ANO": "Ano", "VENDAS": "Volume (m³)"},
                    title=f"Evolução Anual do Volume em {uf_unica} (m³)",
                    color_continuous_scale="Purples",
                    hover_data={"VENDAS": ":,.2f"},
                )
                fig_bar_ano.update_layout(yaxis_tickformat=",.2f")
                fig_bar_ano.update_layout(FORMATO_NUMERO_BR)
                st.plotly_chart(fig_bar_ano, use_container_width=True)
                st.info(
                    f"💡 **O que este gráfico mostra:** Compara o volume total"
                    f" de **{prod}** vendido em **{uf_unica}** em cada ano"
                    " individualmente.\n\n📌 **Observações:** A cor mais"
                    " intensa e a altura da barra destacam os anos com maior"
                    " consumo no estado."
                )

                st.markdown("---")

                # Gráfico 2: Linha do tempo de Evolução Histórica
                st.subheader(f"2. Linha do Tempo Histórica ({uf_unica})")
                fig_linha_uf = px.line(
                    df_ano_uf,
                    x="ANO",
                    y="VENDAS",
                    markers=True,
                    labels={"ANO": "Ano", "VENDAS": "Volume (m³)"},
                    title=f"Tendência do Consumo de {prod} ({uf_unica})",
                    hover_data={"VENDAS": ":,.2f"},
                )
                fig_linha_uf.update_layout(yaxis_tickformat=",.2f")
                fig_linha_uf.update_layout(FORMATO_NUMERO_BR)
                st.plotly_chart(fig_linha_uf, use_container_width=True)
                st.info(
                    f"💡 **O que este gráfico mostra:** Exibe a linha de"
                    f" tendência histórica de vendas de **{prod}** em"
                    f" **{uf_unica}**.\n\n📌 **Observações:** Facilita a"
                    " visualização de oscilações contínuas, períodos de crise"
                    " ou momentos de expansão do mercado local."
                )

            # =========================================================
            # CASO 2: UMA REGIÃO ESPECÍFICA SELECIONADA
            # =========================================================
            elif regiao_escolhida != "Todas as Regiões":
                st.header(f"⛽ Análise Regional ({regiao_escolhida}): {prod}")

                max_uf_prod = (
                    df_prod.groupby("UNIDADE DA FEDERAÇÃO")["VENDAS"]
                    .sum()
                    .idxmax()
                )

                m1, m2, m3 = st.columns(3)
                m1.metric(
                    "Volume Acumulado na Região", f"{fmt_br(vol_total_prod)} m³"
                )
                m2.metric(
                    "Média Mensal por Registro", f"{fmt_br(vol_med_prod)} m³"
                )
                m3.metric("Maior Consumidor da Região", max_uf_prod)

                st.markdown("---")

                # Gráfico 1: Comparação por Estado (Barras)
                st.subheader(
                    f"1. Volume de Vendas por Estado na Região"
                    f" {regiao_escolhida}"
                )
                df_prod_uf = (
                    df_prod.groupby("UNIDADE DA FEDERAÇÃO", as_index=False)[
                        "VENDAS"
                    ]
                    .sum()
                    .sort_values(by="VENDAS", ascending=False)
                )

                fig_bar_uf = px.bar(
                    df_prod_uf,
                    x="UNIDADE DA FEDERAÇÃO",
                    y="VENDAS",
                    color="VENDAS",
                    labels={
                        "UNIDADE DA FEDERAÇÃO": "Estado (UF)",
                        "VENDAS": "Volume (m³)",
                    },
                    title=(
                        f"Volume Total de {prod} Vendido por Estado ("
                        f"{regiao_escolhida})"
                    ),
                    color_continuous_scale="Viridis",
                    hover_data={"VENDAS": ":,.2f"},
                )
                fig_bar_uf.update_layout(yaxis_tickformat=",.2f")
                fig_bar_uf.update_layout(FORMATO_NUMERO_BR)
                st.plotly_chart(fig_bar_uf, use_container_width=True)
                st.info(
                    f"💡 **O que este gráfico mostra:** Compara o volume"
                    f" total de **{prod}** consumido por cada estado dentro da"
                    f" região **{regiao_escolhida}**.\n\n📌"
                    " **Observações:** A altura das barras permite identificar"
                    " o ranking dos estados de maior consumo na região."
                )

                st.markdown("---")

                # Gráfico 2: Evolução Temporal por Estado
                st.subheader(
                    f"2. Evolução Histórica de {prod} por Estado"
                    f" ({regiao_escolhida})"
                )
                df_prod_ano_uf = df_prod.groupby(
                    ["ANO", "UNIDADE DA FEDERAÇÃO"], as_index=False
                )["VENDAS"].sum()

                fig_linha_uf = px.line(
                    df_prod_ano_uf,
                    x="ANO",
                    y="VENDAS",
                    color="UNIDADE DA FEDERAÇÃO",
                    markers=True,
                    labels={
                        "ANO": "Ano",
                        "VENDAS": "Volume (m³)",
                        "UNIDADE DA FEDERAÇÃO": "Estado",
                    },
                    title=(
                        f"Evolução Temporal de {prod} nos Estados de"
                        f" {regiao_escolhida}"
                    ),
                    hover_data={"VENDAS": ":,.2f"},
                )
                fig_linha_uf.update_layout(yaxis_tickformat=",.2f")
                fig_linha_uf.update_layout(FORMATO_NUMERO_BR)
                st.plotly_chart(fig_linha_uf, use_container_width=True)
                st.info(
                    f"💡 **O que este gráfico mostra:** Exibe uma linha para"
                    f" cada **Estado** da região **{regiao_escolhida}**,"
                    f" acompanhando a evolução das vendas de **{prod}** ao"
                    " longo do tempo.\n\n📌 **Observações:** Permite comparar"
                    " o crescimento e comportamento de consumo de cada estado"
                    " individualmente."
                )

                st.markdown("---")

                # Gráfico 3: Pizza da Participação dos Estados
                st.subheader(
                    f"3. Participação Percentual dos Estados da Região"
                    f" {regiao_escolhida}"
                )
                fig_pizza_uf = px.pie(
                    df_prod_uf,
                    names="UNIDADE DA FEDERAÇÃO",
                    values="VENDAS",
                    title=(
                        f"Divisão do Mercado de {prod} entre os Estados de"
                        f" {regiao_escolhida} (%)"
                    ),
                    hole=0.4,
                    hover_data={"VENDAS": ":,.2f"},
                )
                fig_pizza_uf.update_layout(FORMATO_NUMERO_BR)
                st.plotly_chart(fig_pizza_uf, use_container_width=True)
                st.info(
                    f"💡 **O que este gráfico mostra:** Exibe a porcentagem do"
                    f" consumo total de **{prod}** que cabe a cada estado da"
                    f" região **{regiao_escolhida}**.\n\n📌 **Observações:**"
                    " O formato de rosca ajuda a entender a dominância do"
                    " mercado por determinados estados."
                )

            # =========================================================
            # CASO 3: TODAS AS REGIÕES SELECIONADAS (NACIONAL)
            # =========================================================
            else:
                st.header(f"⛽ Análise Nacional: {prod}")

                max_reg_prod = (
                    df_prod.groupby("GRANDE REGIÃO")["VENDAS"].sum().idxmax()
                )

                m1, m2, m3 = st.columns(3)
                m1.metric(
                    "Volume Acumulado Nacional", f"{fmt_br(vol_total_prod)} m³"
                )
                m2.metric(
                    "Média Mensal por Registro", f"{fmt_br(vol_med_prod)} m³"
                )
                m3.metric("Região de Maior Consumo", max_reg_prod)

                st.markdown("---")

                # Gráfico 1: Barras por Região
                st.subheader(f"1. Volume de Vendas de {prod} por Grande Região")
                df_prod_reg = (
                    df_prod.groupby("GRANDE REGIÃO", as_index=False)["VENDAS"]
                    .sum()
                    .sort_values(by="VENDAS", ascending=False)
                )

                fig_bar_reg = px.bar(
                    df_prod_reg,
                    x="GRANDE REGIÃO",
                    y="VENDAS",
                    color="VENDAS",
                    labels={"GRANDE REGIÃO": "Região", "VENDAS": "Volume (m³)"},
                    title=f"Volume Total de {prod} Vendido por Grande Região",
                    color_continuous_scale="Viridis",
                    hover_data={"VENDAS": ":,.2f"},
                )
                fig_bar_reg.update_layout(yaxis_tickformat=",.2f")
                fig_bar_reg.update_layout(FORMATO_NUMERO_BR)
                st.plotly_chart(fig_bar_reg, use_container_width=True)
                st.info(
                    f"💡 **O que este gráfico mostra:** Compara o volume total"
                    f" acumulado de **{prod}** vendido entre as 5 Grandes"
                    " Regiões do Brasil.\n\n📌 **Observações:** Permite"
                    " identificar qual região possui a maior demanda pelo"
                    " produto no âmbito nacional."
                )

                st.markdown("---")

                # Gráfico 2: Rosca por Região
                st.subheader(f"2. Participação Percentual de {prod} por Região")
                fig_pizza_reg = px.pie(
                    df_prod_reg,
                    names="GRANDE REGIÃO",
                    values="VENDAS",
                    title=f"Proporção do Consumo de {prod} por Região (%)",
                    hole=0.4,
                    hover_data={"VENDAS": ":,.2f"},
                )
                fig_pizza_reg.update_layout(FORMATO_NUMERO_BR)
                st.plotly_chart(fig_pizza_reg, use_container_width=True)
                st.info(
                    f"💡 **O que este gráfico mostra:** Exibe a fatia de mercado"
                    f" (%) que cada Grande Região representa no total"
                    f" nacional do combustível **{prod}**.\n\n📌"
                    " **Observações:** Facilita a visualização da divisão"
                    " percentual do mercado."
                )

                st.markdown("---")

                # Gráfico 3: Linha por Região
                st.subheader(f"3. Evolução Histórica de {prod} por Região")
                df_prod_ano_reg = df_prod.groupby(
                    ["ANO", "GRANDE REGIÃO"], as_index=False
                )["VENDAS"].sum()

                fig_linha_reg = px.line(
                    df_prod_ano_reg,
                    x="ANO",
                    y="VENDAS",
                    color="GRANDE REGIÃO",
                    markers=True,
                    labels={
                        "ANO": "Ano",
                        "VENDAS": "Volume Vendido (m³)",
                        "GRANDE REGIÃO": "Região",
                    },
                    title=f"Evolução Temporal de {prod} por Grande Região",
                    hover_data={"VENDAS": ":,.2f"},
                )
                fig_linha_reg.update_layout(yaxis_tickformat=",.2f")
                fig_linha_reg.update_layout(FORMATO_NUMERO_BR)
                st.plotly_chart(fig_linha_reg, use_container_width=True)
                st.info(
                    f"💡 **O que este gráfico mostra:** Exibe uma linha para"
                    f" cada **Grande Região**, mostrando a tendência histórica"
                    f" do consumo de **{prod}** ao longo do tempo.\n\n📌"
                    " **Observações:** Permite comparar visualmente o ritmo de"
                    " crescimento ou retração de cada região ao longo das"
                    " décadas."
                )

    # =========================================================
    # EXPORTAÇÃO DOS DADOS FILTRADOS
    # =========================================================
    st.markdown("---")
    st.subheader("📥 Exportação dos Dados Filtrados")
    st.markdown(
        "Faça o download do conjunto de dados atualmente filtrado acima para"
        " uso em planilha ou relatórios externos:"
    )

    csv_dados = df_filtrado.to_csv(index=False, sep=";").encode("utf-8-sig")
    st.download_button(
        label="📥 Baixar Dados Filtrados em CSV",
        data=csv_dados,
        file_name=f"vendas_combustiveis_{intervalo_anos[0]}_{intervalo_anos[1]}.csv",
        mime="text/csv",
    )

    # =========================================================
    # REGISTRO DO USO DA INTELIGÊNCIA ARTIFICIAL
    # =========================================================
    st.markdown("---")
    st.subheader("🤖 Registro Formal do Uso da Inteligência Artificial")
    st.markdown("""
    Registro de orientação técnica, aprendizado, suporte e otimização geral no projeto:

    * **1. Dúvida/Problema Educacional:** Como utilizar a Inteligência Artificial como ferramenta de aprendizado prático para resolver múltiplos desafios do projeto, entender conceitos de desenvolvimento web com Streamlit/Plotly e otimizar o código final?[cite: 1]
    * **2. Solicitação Realizada:** Pedi auxílio abrangente para **diversas etapas do desenvolvimento**, incluindo o aprendizado de conceitos de visualização de dados, correção de erros, adequação da formatação regional brasileira (`1.900,00`) tanto nos eixos quanto nos *tooltips* (caixas flutuantes ao passar o mouse), estilização visual de gráficos e a otimização geral do código Python.[cite: 1]
    * **3. Conceito Aprendido e Aplicado:** 
      * Estruturação e refatoração de código interativo em Streamlit com cache (`st.cache_data`).
      * Padronização de formatação numérica e internacionalização regional no Plotly via `update_layout(separators=",.")` combinada com `hover_data={"VENDAS": ":,.2f"}` para caixas flutuantes.
      * Aplicação de boas práticas de design de dashboards e tratamento defensivo de dados com Pandas.
    * **4. Validação:** A aplicação passou por um processo completo de otimização e melhoria contínua, resultando em um código mais limpo, eficiente, bem documentado e esteticamente alinhado com as necessidades do projeto.[cite: 1]
    """)

except FileNotFoundError:
    st.error(
        f"⚠️ Arquivo `{CAMINHO_ARQUIVO}` não foi encontrado. Por favor, coloque"
        " o arquivo CSV na mesma pasta deste script Python."
    )
except Exception as e:
    st.error(f"⚠️ Ocorreu um erro ao carregar/processar o arquivo: {e}")
