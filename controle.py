import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configurações de estilo
sns.set(style="whitegrid")

# Carregando o Excel
arquivo = st.file_uploader("📂 Envie seu arquivo Excel com as abas: entrada, saida, investimento", type=["xlsx"])
if arquivo is not None:
    entrada_df = pd.read_excel(arquivo, sheet_name="entrada")
    saida_df = pd.read_excel(arquivo, sheet_name="saida")
    investimento_df = pd.read_excel(arquivo, sheet_name="investimento")

    # Layout de abas
    st.title("Dashboard Financeiro Pessoal")
    tabs = st.tabs(["Entradas", "Saídas", "Investimentos"])

    # --- ABA ENTRADA ---
    with tabs[0]:
        st.header("Análise de Entradas")

        entrada_df["Total Entradas"] = entrada_df["Salário"] + entrada_df["Outras Entradas"]

        # Linha de entradas
        st.subheader("Total de Entradas por Mês")
        st.line_chart(entrada_df.set_index("Mês")["Total Entradas"])

        # Pizza de proporção
        st.subheader("Proporção entre Salário e Outras Entradas")
        media_entradas = entrada_df[["Salário", "Outras Entradas"]].mean()
        fig1, ax1 = plt.subplots()
        ax1.pie(media_entradas, labels=media_entradas.index, autopct='%1.1f%%', startangle=90)
        st.pyplot(fig1)

        # Barras comparativas
        st.subheader("Comparativo por Categoria")
        st.bar_chart(entrada_df.set_index("Mês")[["Salário", "Outras Entradas"]])

    # --- ABA SAIDA ---
    with tabs[1]:
        st.header("Análise de Saídas")

        saida_df["Total Gastos"] = saida_df.drop(columns="Mês").sum(axis=1)
        
        # Linha de gastos
        st.subheader("Gastos Totais por Mês")
        st.line_chart(saida_df.set_index("Mês")["Total Gastos"])

        # Barras por categoria
        st.subheader("Gastos por Categoria")
        st.bar_chart(saida_df.set_index("Mês").drop(columns=["Total Gastos"]))

        # Pizza de distribuição
        st.subheader("Distribuição Média de Gastos")
        media_gastos = saida_df.drop(columns=["Mês", "Total Gastos"]).mean()
        fig2, ax2 = plt.subplots()
        ax2.pie(media_gastos, labels=media_gastos.index, autopct='%1.1f%%', startangle=90)
        st.pyplot(fig2)

    # --- ABA INVESTIMENTO ---
    with tabs[2]:
        st.header("Análise de Investimentos e Crescimento")

        # Crescimento do saldo
        st.subheader("Evolução do Saldo Total")
        st.line_chart(investimento_df.set_index("Mês")["Saldo Total"])

        # Comparativo investimento vs saldo
        st.subheader("Investimento vs Saldo")
        st.area_chart(investimento_df.set_index("Mês")[["Investimento", "Saldo Total"]])

        # Quanto gasta x quanto guarda
        st.subheader("Gastos vs Investimentos")
        comparativo = pd.DataFrame({
            "Gastos": saida_df["Total Gastos"],
            "Investimentos": investimento_df["Investimento"]
        }, index=saida_df["Mês"])
        st.bar_chart(comparativo)

        # Projeção simples: saldo futuro
        st.subheader("Projeção de Saldo Futuro")
        media_invest = investimento_df["Investimento"].mean()
        saldo_atual = investimento_df["Saldo Total"].iloc[-1]
        projecao = [saldo_atual + media_invest * i for i in range(1, 7)]
        projecao_df = pd.DataFrame({
            "Mês": [f"+{i}m" for i in range(1, 7)],
            "Saldo Projetado": projecao
        })
        st.line_chart(projecao_df.set_index("Mês"))
