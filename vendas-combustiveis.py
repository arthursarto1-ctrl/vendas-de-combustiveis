import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Dashboard - Vendas de Combustíveis",
    layout="wide"
)

# =========================================================
# CAMINHO DIRETO DO ARQUIVO
# =========================================================
CAMINHO_ARQUIVO = "vendas-combustiveis-m3-1990-2025.csv"

# =========================================================
# APRESENTAÇÃO E EXPLICAÇÃO DA APLICAÇÃO
# =========================================================
st.title("⛽ Dashboard de Vendas de Combustíveis no Brasil")
st.markdown("""
**Tema:** Economia e Transporte (Consumo de Combustíveis)  
**Fonte dos Dados:** Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP) / dados.gov.br  
---

Feito por: Arthur Sartori Cavalcanti

Orientado por:Felipe Garbin

---

### 📖 Sobre a Aplicação
Esta aplicação interativa foi desenvolvida para analisar e explorar a distribuição histórica das vendas de combustíveis nas diferentes regiões do Brasil.

**Como navegar no Dashboard:**
* **Barra Lateral (Sidebar):** Permite visualizar o diagnóstico automático da base de dados carregada.
* **Aba 🌐 Geral (Todos):** Apresenta a visão macro do mercado brasileiro, comparando o consumo entre todos os tipos de combustíveis, suas tendências anuais acumuladas e a fatia regional total.
* **Abas Individuais (⛽ Produto):** Permitem focar em um combustível específico para analisar sua presença em cada Grande Região por meio de tabelas, gráficos de barras, gráficos de tendência temporal e gráficos de pizza/rosca.

---

### 🎯 Perguntas da Análise:
1. **Pergunta 1:** Quais tipos de combustíveis possuem o maior volume acumulado de vendas no país?
2. **Pergunta 2:** Como o volume de vendas de combustíveis se distribui entre as Grandes Regiões brasileiras?
3. **Pergunta 3:** Qual é a tendência de evolução do volume de vendas ao longo dos anos?
""")

st.markdown("---")

# =========================================================
# CARREGAMENTO AUTOMÁTICO DOS DADOS
# =========================================================
st.sidebar.header("📁 Base de Dados")

try:
    df = pd.read_csv(CAMINHO_ARQUIVO, sep=None, engine='python')
    st.sidebar.info(f"Carregado de: `{CAMINHO_ARQUIVO}`")

    # Limpeza do nome das colunas (remoção de caracteres invisíveis UTF-8)
    df.columns = df.columns.str.replace('\ufeff', '').str.strip()
    
    colunas_necessarias = ['ANO', 'MÊS', 'GRANDE REGIÃO', 'UNIDADE DA FEDERAÇÃO', 'PRODUTO', 'VENDAS']
    for col in colunas_necessarias:
        if col not in df.columns:
            st.error(f"Erro: A coluna '{col}' não foi encontrada na base de dados.")
            st.stop()
            
    # Tratamento da coluna de vendas (texto com vírgula -> float)
    df['VENDAS'] = df['VENDAS'].astype(str).str.replace(',', '.').str.strip()
    df['VENDAS'] = pd.to_numeric(df['VENDAS'], errors='coerce')
    
    # Diagnóstico da base na barra lateral
    st.sidebar.subheader("🔍 Diagnóstico da Base")
    v_nulos = df.isnull().sum().sum()
    v_duplicados = df.duplicated().sum()
    st.sidebar.text(f"• Valores Nulos: {v_nulos}")
    st.sidebar.text(f"• Duplicados: {v_duplicados}")
    st.sidebar.text(f"• Colunas: {df.shape[1]}")
    st.sidebar.text(f"• Registros: {df.shape[0]:,}")
    
    # Lista de combustíveis únicos
    produtos_unicos = sorted(list(df['PRODUTO'].unique()))
    
    # =========================================================
    # ESTRUTURA EM ABAS (TODOS + CADA COMBUSTÍVEL INDIVIDUAL)
    # =========================================================
    
    nomes_abas = ["🌐 Geral (Todos)"] + [f"⛽ {prod}" for prod in produtos_unicos]
    abas = st.tabs(nomes_abas)
    
    # ---------------------------------------------------------
    # ABA 1: GERAL (TODOS OS COMBUSTÍVEIS)
    # ---------------------------------------------------------
    with abas[0]:
        st.header("📊 Visão Geral do Mercado Nacional")
        
        # RESUMO GERAL DA ABA
        st.markdown("""
        > **Resumo da Aba:**  
        > Nesta aba, podemos observar o panorama completo do mercado nacional de combustíveis, reunindo todas as categorias vendidas no Brasil e suas distribuições.  
        > **O que os dados mostram e o que é possível perceber:** Os dados mostram a liderança dos combustíveis de grande consumo (como Diesel e Gasolina) sobre os demais e indicam que a região Sudeste concentra o maior volume absoluto de vendas do país.
        """)
        st.markdown("---")
        
        # Resumo agrupado
        df_tabela_geral = df.groupby("PRODUTO", as_index=False).agg(
            Volume_Total_m3=("VENDAS", "sum"),
            Media_Mensal_m3=("VENDAS", "mean"),
            Registros=("VENDAS", "count")
        ).sort_values(by="Volume_Total_m3", ascending=False)
        
        total_geral = df_tabela_geral["Volume_Total_m3"].sum()
        df_tabela_geral["Participacao_%"] = (df_tabela_geral["Volume_Total_m3"] / total_geral * 100).round(2)
        
        # Tabela formatada
        tabela_formatada = df_tabela_geral.copy()
        tabela_formatada["Volume_Total_m3"] = tabela_formatada["Volume_Total_m3"].apply(lambda x: f"{x:,.2f}")
        tabela_formatada["Media_Mensal_m3"] = tabela_formatada["Media_Mensal_m3"].apply(lambda x: f"{x:,.2f}")
        tabela_formatada["Participacao_%"] = tabela_formatada["Participacao_%"].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(tabela_formatada, use_container_width=True)
        
        st.markdown("---")
        
        # Indicadores Numéricos Gerais
        c1, c2, c3 = st.columns(3)
        c1.metric("Quantidade Total de Registros", f"{df.shape[0]:,}")
        c2.metric("Volume Total Vendido", f"{total_geral:,.2f} m³")
        c3.metric("Média por Registro", f"{df['VENDAS'].mean():,.2f} m³")
        
        st.markdown("---")
        
        # Gráfico 1: Comparativo por Produto
        st.subheader("1. Volume Total Vendido por Tipo de Produto")
        fig_barras_geral = px.bar(
            df_tabela_geral,
            x="PRODUTO",
            y="Volume_Total_m3",
            labels={"PRODUTO": "Combustível", "Volume_Total_m3": "Volume Vendido (m³)"},
            title="Volume Acumulado de Vendas por Categoria (m³)",
            color="Volume_Total_m3",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_barras_geral, use_container_width=True)
        
        st.markdown("""
        O gráfico apresenta a soma total de vendas de cada combustível no Brasil ao longo de toda a base de dados.

        Os principais resultados observados são: a liderança do Óleo Diesel e da Gasolina C, que apresentam volumes muito superiores aos demais produtos. Combustíveis como o Querosene de Aviação e o Óleo Combustível ocupam as posições mais baixas no volume acumulado.
        """)
        
        with st.expander("💡 Resposta referente a este gráfico (Pergunta 1)"):
            st.markdown("**Resposta:** O **Óleo Diesel** possui o maior volume acumulado de vendas no país, seguido diretamente pela **Gasolina C**. Juntas, essas duas categorias lideram amplamente o consumo nacional de combustíveis.")
        
        st.markdown("---")
        
        # Gráfico 2: Evolução Histórica Geral
        st.subheader("2. Evolução Histórica de Vendas por Ano")
        df_linha_geral = df.groupby(["ANO", "PRODUTO"], as_index=False)["VENDAS"].sum()
        
        fig_linha_geral = px.line(
            df_linha_geral,
            x="ANO",
            y="VENDAS",
            color="PRODUTO",
            markers=True,
            title="Evolução Temporal do Volume Vendido (m³)"
        )
        st.plotly_chart(fig_linha_geral, use_container_width=True)
        
        st.markdown("""
        O gráfico mostra a linha do tempo com a quantidade de combustível vendida por ano no país para cada categoria.

        Os principais resultados observados são: uma tendência geral de crescimento nas vendas ao longo dos anos. O Óleo Diesel e a Gasolina C mantiveram-se no topo da série histórica durante todo o período registrado.
        """)
        
        with st.expander("💡 Resposta referente a este gráfico (Pergunta 3)"):
            st.markdown("**Resposta:** A tendência de evolução ao longo dos anos é **ascendente (de crescimento)** para os principais combustíveis comercializados, mantendo o Óleo Diesel e a Gasolina C constantemente no topo do volume anual.")
        
        st.markdown("---")
        
        # Gráfico 3: Participação Regional Geral
        st.subheader("3. Distribuição Geral de Vendas por Região")
        df_regiao_geral = df.groupby("GRANDE REGIÃO", as_index=False)["VENDAS"].sum().sort_values(by="VENDAS", ascending=False)
        
        fig_rosca_geral = px.pie(
            df_regiao_geral,
            names="GRANDE REGIÃO",
            values="VENDAS",
            title="Participação Percentual por Grande Região",
            hole=0.4
        )
        st.plotly_chart(fig_rosca_geral, use_container_width=True)
        
        st.markdown("""
        O gráfico mostra a fatia percentual que cada uma das cinco Grandes Regiões brasileiras representa no volume total vendido.

        Os principais resultados observados são: a Região Sudeste registra a maior fatia do consumo nacional, seguida pelas regiões Sul e Nordeste. As regiões Centro-Oeste e Norte possuem as menores porcentagens na soma de todos os combustíveis.
        """)
        
        with st.expander("💡 Resposta referente a este gráfico (Pergunta 2)"):
            st.markdown("**Resposta:** O volume de vendas distribui-se de forma desigual entre as regiões, concentrando-se fortemente na **Região Sudeste** (que detém quase metade das vendas), seguida do **Sul** e **Nordeste**, enquanto **Centro-Oeste** e **Norte** registram as menores fatias do mercado.")

    # ---------------------------------------------------------
    # ABAS INDIVIDUAIS POR TIPO DE COMBUSTÍVEL
    # ---------------------------------------------------------
    for i, prod in enumerate(produtos_unicos):
        with abas[i + 1]:
            st.header(f"⛽ Análise Regional: {prod}")
            
            # Filtro para o combustível específico
            df_prod = df[df['PRODUTO'] == prod]
            
            # Métricas rápidas do produto
            vol_total_prod = df_prod['VENDAS'].sum()
            vol_med_prod = df_prod['VENDAS'].mean()
            max_reg_prod = df_prod.groupby("GRANDE REGIÃO")["VENDAS"].sum().idxmax()
            
            # RESUMO DA ABA INDIVIDUAL
            st.markdown(f"""
            > **Resumo da Aba:**  
            > Nesta aba, podemos observar os dados específicos do combustível **{prod}** detalhados entre as regiões do Brasil.  
            > **O que os dados mostram e o que é possível perceber:** Os dados mostram a distribuição do volume de vendas por Grande Região, permitindo perceber qual região consome a maior parte de **{prod}** e como essas vendas variaram com o passar dos anos.
            """)
            st.markdown("---")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Volume Acumulado do Produto", f"{vol_total_prod:,.2f} m³")
            m2.metric("Média Mensal por Estado", f"{vol_med_prod:,.2f} m³")
            m3.metric("Região de Maior Consumo", max_reg_prod)
            
            st.markdown("---")
            
            # Gráfico Regional 1: Total por Região (Barras)
            st.subheader(f"1. Volume de Vendas de {prod} por Região")
            df_prod_reg = df_prod.groupby("GRANDE REGIÃO", as_index=False)["VENDAS"].sum().sort_values(by="VENDAS", ascending=False)
            
            fig_bar_reg = px.bar(
                df_prod_reg,
                x="GRANDE REGIÃO",
                y="VENDAS",
                color="VENDAS",
                labels={"GRANDE REGIÃO": "Região", "VENDAS": "Volume (m³)"},
                title=f"Volume Total de {prod} Vendido por Grande Região",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig_bar_reg, use_container_width=True)
            
            reg_maior_nome = df_prod_reg.iloc[0]["GRANDE REGIÃO"]
            reg_maior_val = df_prod_reg.iloc[0]["VENDAS"]
            
            st.markdown(f"""
            O gráfico exibe o volume acumulado total das vendas do combustível **{prod}** em cada Grande Região.

            Os principais resultados observados são: a região **{reg_maior_nome}** possui o maior valor acumulado de vendas com **{reg_maior_val:,.2f} m³**. O gráfico deixa evidente a diferença na quantidade consumida entre a primeira colocada e as demais regiões do país.
            """)
            
            with st.expander(f"💡 Resposta regional de {prod} (Pergunta 2)"):
                st.markdown(f"**Resposta:** Para o combustível **{prod}**, a maior concentração de vendas ocorre na **Região {reg_maior_nome}**, registrando o maior volume total entre todas as regiões comparadas.")
            
            st.markdown("---")
            
            # Gráfico Regional 2: Distribuição Percentual por Região (Pizza/Rosca)
            st.subheader(f"2. Participação Percentual de {prod} por Região")
            
            fig_pizza_reg = px.pie(
                df_prod_reg,
                names="GRANDE REGIÃO",
                values="VENDAS",
                title=f"Proporção do Consumo de {prod} por Região (%)",
                hole=0.4
            )
            st.plotly_chart(fig_pizza_reg, use_container_width=True)
            
            pct_maior = (reg_maior_val / vol_total_prod) * 100
            
            st.markdown(f"""
            O gráfico apresenta a divisão em porcentagem do volume total vendido de **{prod}** entre as regiões.

            Os principais resultados observados são: a maior fatia pertence à região **{reg_maior_nome}**, correspondendo a **{pct_maior:.1f}%** das vendas. As fatias restantes destacam a proporção individual de consumo das demais regiões brasileiras.
            """)
            
            with st.expander(f"💡 Resposta de participação percentual de {prod} (Pergunta 2)"):
                st.markdown(f"**Resposta:** A Região **{reg_maior_nome}** responde por **{pct_maior:.1f}%** de todas as vendas de **{prod}** no país, evidenciando sua liderança proporcional no mercado desse produto.")
            
            st.markdown("---")
            
            # Gráfico Regional 3: Evolução Histórica por Região (Linha)
            st.subheader(f"3. Evolução Histórica de Vendas de {prod} por Região")
            df_prod_ano_reg = df_prod.groupby(["ANO", "GRANDE REGIÃO"], as_index=False)["VENDAS"].sum()
            
            fig_linha_reg = px.line(
                df_prod_ano_reg,
                x="ANO",
                y="VENDAS",
                color="GRANDE REGIÃO",
                markers=True,
                labels={"ANO": "Ano", "VENDAS": "Volume Vendido (m³)", "GRANDE REGIÃO": "Região"},
                title=f"Evolução Temporal de {prod} por Grande Região"
            )
            st.plotly_chart(fig_linha_reg, use_container_width=True)
            
            st.markdown(f"""
            O gráfico de linhas acompanha o desempenho anual das vendas de **{prod}** ao longo do tempo em cada região.

            Os principais resultados observados são: o comportamento das vendas ao longo dos anos, identificando os períodos de aumento ou retração no consumo. A região líder mantém sua posição nas partes mais altas do gráfico na maior parte dos anos.
            """)
            
            with st.expander(f"💡 Resposta da evolução temporal de {prod} (Pergunta 3)"):
                st.markdown(f"**Resposta:** A evolução das vendas de **{prod}** mostra o histórico do produto ao longo do tempo, mantendo a Região **{reg_maior_nome}** no nível superior das vendas anuais.")

    # =========================================================
    # REGISTRO DO USO DA INTELIGÊNCIA ARTIFICIAL
    # =========================================================
    st.markdown("---")
    st.subheader("🤖 Registro Formal do Uso da Inteligência Artificial")
    st.markdown("""
    Registro de apoio tecnológico utilizado durante a elaboração do projeto:

    * **1. Problema Encontrado:** A coluna `VENDAS` trazia números salvos como texto utilizando vírgulas como separadores decimais (`7578,939`), além de o nome das colunas conter caracteres invisíveis de codificação UTF-8 (`\\ufeff`), o que impedia os cálculos no Pandas.
    * **2. Prompt Utilizado:** *"Como organizar a visualização em abas no Streamlit criando uma aba geral e abas dinâmicas por produto?"*
    * **3. Sugestão da IA:** Utilização do recurso `st.tabs()` iterando sobre a lista de produtos únicos do DataFrame (`df['PRODUTO'].unique()`).
    * **4. Validação do Grupo:** O grupo aplicou a estrutura de abas, conferiu o correto isolamento dos dados regionais por combustível e validou se a soma dos totais por aba bate com o acumulado nacional.
    """)

except Exception as e:
    st.error(f"⚠️ O arquivo `{CAMINHO_ARQUIVO}` não foi encontrado na raiz do projeto ou ocorreu um erro na leitura. Certifique-se de que o arquivo esteja com o nome exato.")
