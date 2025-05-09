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

    tabs = st.tabs(["💰 Entradas", "💸 Saídas", "📈 Investimentos","🔍 Feedback Inteligente"])

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
    # --- FEEDBACK INTELIGENTE ---
    


    with tabs[3]:
        st.header("🔍 Análise e Recomendações Personalizadas")

        if len(saida_df) >= 3 and len(investimento_df) >= 3:
            categorias_gastos = saida_df.drop(columns=["Mês", "Total Gastos"])
            media_3m = categorias_gastos.tail(3).mean()
            ultimo_mes = categorias_gastos.tail(1).iloc[0]

            st.subheader("📌 Gastos em Foco")

            feedback_exibido = False
            for categoria in categorias_gastos.columns:
                gasto_mes = ultimo_mes[categoria]
                media_categoria = media_3m[categoria]

                if gasto_mes > media_categoria * 1.15:
                    excesso = gasto_mes - media_categoria
                    economia_potencial = excesso * 0.25
                    st.markdown(f"""
                    🔴 **{categoria}** teve um gasto acima da média em **{(gasto_mes - media_categoria) / media_categoria:.0%}** comparado aos últimos 3 meses.  
                    👉 Considere reduzir em **R${economia_potencial:,.2f}**, podendo investir esse valor.
                    """)
                    feedback_exibido = True

            if not feedback_exibido:
                st.success("✅ Parabéns! Os gastos deste mês estão dentro da média. Continue assim! 💪")

            st.divider()

            st.subheader("🎯 Meta de Economia")
            media_total = saida_df["Total Gastos"].tail(3).mean()
            meta_economia = media_total * 0.1

            if saida_df["Total Gastos"].iloc[-1] > media_total * 1.1:
                st.markdown(f"""
                📊 Sua média de gastos mensais foi de **R${media_total:,.2f}**.  
                💡 Recomendamos uma meta de economia de **10%**, equivalente a **R${meta_economia:,.2f}** no próximo mês.
                """)
            else:
                st.info("👍 Seus gastos totais estão sob controle. Mantenha o ritmo!")

            st.divider()

            st.subheader("📈 Reforço nos Investimentos")
            media_invest = investimento_df["Investimento"].tail(3).mean()
            invest_mes_atual = investimento_df["Investimento"].iloc[-1]

            if invest_mes_atual < media_invest * 0.9:
                reforco = media_invest * 0.2
                st.markdown(f"""
                📉 Neste mês, os investimentos ficaram abaixo da média (**R${invest_mes_atual:,.2f}** vs **R${media_invest:,.2f}**).  
                💡 Considere aumentar em **R${reforco:,.2f}** para manter o ritmo de crescimento.
                """)
            else:
                st.success("📈 Ótimo trabalho! Seus investimentos estão consistentes ou acima da média.")
        else:
            st.warning("⚠️ É necessário pelo menos 3 meses de dados para gerar análises inteligentes.")
