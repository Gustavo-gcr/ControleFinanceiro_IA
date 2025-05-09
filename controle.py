import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# Estilo
sns.set(style="whitegrid")

# Upload
st.set_page_config(page_title="Dashboard Financeiro", layout="wide")
st.title("📊 Dashboard Financeiro Pessoal")
arquivo = st.file_uploader("📂 Envie seu arquivo Excel com as abas: entrada, saida, investimento", type=["xlsx"])

if arquivo is not None:
    entrada_df = pd.read_excel(arquivo, sheet_name="entrada")
    saida_df = pd.read_excel(arquivo, sheet_name="saida")
    investimento_df = pd.read_excel(arquivo, sheet_name="investimento")

    opcao = st.radio("🔎 Visualizar:", ["Histórico completo", "Mês atual"])
    if opcao == "Mês atual":
        entrada_df = entrada_df.tail(1)
        saida_df = saida_df.tail(1)
        investimento_df = investimento_df.tail(1)

    tabs = st.tabs(["💰 Entradas", "💸 Saídas", "📈 Investimentos"])

    # --- ENTRADAS ---
    with tabs[0]:
        st.header("💰 Análise de Entradas")
        entrada_df["Total Entradas"] = entrada_df["Salário"] + entrada_df["Outras Entradas"]

        st.subheader("📆 Total de Entradas por Mês")
        fig_entrada = px.line(entrada_df, x="Mês", y="Total Entradas", markers=True, text="Total Entradas")
        fig_entrada.update_traces(textposition="top center")
        st.plotly_chart(fig_entrada, use_container_width=True)

        st.subheader("📊 Proporção entre Salário e Outras Entradas")
        media_entradas = entrada_df[["Salário", "Outras Entradas"]].mean()
        fig1, ax1 = plt.subplots()
        ax1.pie(media_entradas, labels=media_entradas.index, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        st.pyplot(fig1)

        st.subheader("📋 Comparativo por Categoria")
        fig_cat = px.bar(entrada_df, x="Mês", y=["Salário", "Outras Entradas"], barmode="group", text_auto=True)
        fig_cat.update_traces(textposition="outside")
        st.plotly_chart(fig_cat, use_container_width=True)

    # --- SAÍDAS ---
    with tabs[1]:
        st.header("💸 Análise de Saídas")
        saida_df["Total Gastos"] = saida_df.drop(columns="Mês").sum(axis=1)

        st.subheader("📆 Gastos Totais por Mês")
        fig_gastos = px.line(saida_df, x="Mês", y="Total Gastos", markers=True, text="Total Gastos")
        fig_gastos.update_traces(textposition="top center")
        st.plotly_chart(fig_gastos, use_container_width=True)

        st.subheader("📋 Gastos por Categoria")
        categorias = saida_df.drop(columns=["Mês", "Total Gastos"])
        fig_cat = px.bar(saida_df, x="Mês", y=categorias.columns, barmode="group", text_auto=True)
        fig_cat.update_traces(textposition="outside")
        st.plotly_chart(fig_cat, use_container_width=True)

        st.subheader("📊 Distribuição Média de Gastos")
        media_gastos = categorias.mean()
        fig2, ax2 = plt.subplots()
        ax2.pie(media_gastos, labels=media_gastos.index, autopct='%1.1f%%', startangle=90)
        ax2.axis('equal')
        st.pyplot(fig2)

    # --- INVESTIMENTOS ---
    with tabs[2]:
        st.header("📈 Análise de Investimentos e Crescimento")

        st.subheader("📆 Evolução do Saldo Total")
        fig_saldo = px.line(investimento_df, x="Mês", y="Saldo Total", markers=True, text="Saldo Total")
        fig_saldo.update_traces(textposition="top center")
        st.plotly_chart(fig_saldo, use_container_width=True)

        

        st.subheader("📊 Gastos vs Investimentos")
        comparativo = pd.DataFrame({
            "Mês": saida_df["Mês"],
            "Gastos": saida_df["Total Gastos"].values,
            "Investimentos": investimento_df["Investimento"].values
        })

        fig_bar = go.Figure()

        fig_bar.add_trace(go.Bar(
            x=comparativo["Mês"],
            y=comparativo["Gastos"],
            name="Gastos",
            text=comparativo["Gastos"].apply(lambda x: f"R${x:,.2f}"),
            textposition="outside",
            marker_color="indianred"
        ))

        fig_bar.add_trace(go.Bar(
            x=comparativo["Mês"],
            y=comparativo["Investimentos"],
            name="Investimentos",
            text=comparativo["Investimentos"].apply(lambda x: f"R${x:,.2f}"),
            textposition="outside",
            marker_color="seagreen"
        ))

        fig_bar.update_layout(
            barmode="group",
            title="Comparativo: Gastos x Investimentos por Mês",
            xaxis_title="Mês",
            yaxis_title="Valor (R$)",
            legend_title="Categoria",
            uniformtext_minsize=8,
            uniformtext_mode="hide"
        )

        st.plotly_chart(fig_bar, use_container_width=True)

      
        st.subheader("🔮 Projeção de Saldo Futuro (6 meses)")
        media_invest = investimento_df["Investimento"].mean()
        saldo_atual = investimento_df["Saldo Total"].iloc[-1]
        projecao = [saldo_atual + media_invest * i for i in range(1, 7)]
        projecao_df = pd.DataFrame({
            "Mês": [f"+{i}m" for i in range(1, 7)],
            "Saldo Projetado": projecao
        })
        fig_proj = px.line(projecao_df, x="Mês", y="Saldo Projetado", markers=True, text="Saldo Projetado")
        fig_proj.update_traces(textposition="top center")
        st.plotly_chart(fig_proj, use_container_width=True)
