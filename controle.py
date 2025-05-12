import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI

# === CONFIGURAÇÕES ===
st.set_page_config(page_title="Dashboard Financeiro", layout="wide")
st.title("📊 Dashboard Financeiro Pessoal")


client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

# === UPLOAD DO EXCEL ===
arquivo = st.file_uploader("📂 Envie seu arquivo Excel com abas: entrada, saida, investimento", type=["xlsx"])

if arquivo:
    # Lê as abas
    entrada_df = pd.read_excel(arquivo, sheet_name="entrada")
    saida_df = pd.read_excel(arquivo, sheet_name="saida")
    investimento_df = pd.read_excel(arquivo, sheet_name="investimento")

    # Escolha vista
    opcao = st.radio("🔎 Visualizar:", ["Histórico completo", "Mês atual"])
    if opcao == "Mês atual":
        entrada_df = entrada_df.tail(1)
        saida_df = saida_df.tail(1)
        investimento_df = investimento_df.tail(1)

    tabs = st.tabs(["💰 Entradas", "💸 Saídas", "📈 Investimentos", "Feedback Moderado ","🤖 Feedback Avançado"])

    # === TAB ENTRADAS ===
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

    # === TAB SAÍDAS ===
    with tabs[1]:
        st.header("💸 Análise de Saídas")
        saida_df["Total Gastos"] = saida_df.drop(columns="Mês").sum(axis=1)

        st.subheader("📆 Gastos Totais por Mês")
        fig_gastos = px.line(saida_df, x="Mês", y="Total Gastos", markers=True, text="Total Gastos")
        fig_gastos.update_traces(textposition="top center")
        st.plotly_chart(fig_gastos, use_container_width=True)

        st.subheader("📋 Gastos por Categoria")
        categorias = saida_df.drop(columns=["Mês", "Total Gastos"])
        fig_cat2 = px.bar(saida_df, x="Mês", y=categorias.columns, barmode="group", text_auto=True)
        fig_cat2.update_traces(textposition="outside")
        st.plotly_chart(fig_cat2, use_container_width=True)

        st.subheader("📊 Distribuição Média de Gastos")
        media_gastos = categorias.mean()
        fig2, ax2 = plt.subplots()
        ax2.pie(media_gastos, labels=media_gastos.index, autopct='%1.1f%%', startangle=90)
        ax2.axis('equal')
        st.pyplot(fig2)

    # === TAB INVESTIMENTOS ===
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
        fig_bar.add_trace(go.Bar(x=comparativo["Mês"], y=comparativo["Gastos"], name="Gastos"))
        fig_bar.add_trace(go.Bar(x=comparativo["Mês"], y=comparativo["Investimentos"], name="Investimentos"))
        fig_bar.update_layout(barmode="group", title="Gastos x Investimentos por Mês")
        st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("🔮 Projeção de Saldo Futuro (6 meses)")
        media_invest = investimento_df["Investimento"].mean()
        saldo_atual = investimento_df["Saldo Total"].iloc[-1]
        projecao = [round(saldo_atual + media_invest * i, 2) for i in range(1, 7)]
        projecao_df = pd.DataFrame({
            "Mês": [f"+{i}m" for i in range(1, 7)],
            "Saldo Projetado": projecao
        })
        projecao_df["Texto"] = projecao_df["Saldo Projetado"].apply(
            lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        fig_proj = px.line(projecao_df, x="Mês", y="Saldo Projetado", markers=True, text="Texto")
        fig_proj.update_traces(textposition="top center")
        st.plotly_chart(fig_proj, use_container_width=True)

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
            
with tabs[4]:
    st.header("🤖 Feedback com IA")
    st.markdown("📄 Gerando análise personalizada dos seus dados financeiros...")

    ultimos_gastos = saida_df.tail(1).drop(columns=["Mês"]).to_dict(orient="records")[0]
    ultimos_invest = investimento_df.tail(1).to_dict(orient="records")[0]

    prompt = f"""
    Você é um assistente financeiro pessoal. Dado os dados abaixo, forneça conselhos personalizados e diretos.

    Últimos gastos:
    {ultimos_gastos}

    Últimos investimentos:
    {ultimos_invest}

    Dê sugestões específicas de economia e investimento, apontando onde a pessoa pode melhorar.
    """

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Você é um especialista em finanças pessoais."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.7,
            max_tokens=700
        )
        resposta_raw = response.choices[0].message.content


        resposta_formatada = (
            resposta_raw
            .replace("Análise dos Gastos", "🔍 **Análise dos Gastos**")
            .replace("Análise dos Investimentos", "📈 **Análise dos Investimentos**")
            .replace("Conclusão e Sugestões", "✅ **Conclusão e Sugestões**")
            .replace("Sugiero", "💡 Sugiro")  
            .replace("Você", "👉 Você")
            .replace("Reduzir", "🔻 Reduzir")
            .replace("Aumentar", "🔺 Aumentar")
            .replace("Explorar", "🔍 Explorar")
            .replace("Resumo", "📝 Resumo")
            .replace("Em primeiro lugar", "📌 Em primeiro lugar")
            .replace("Em seguida", "📎 Em seguida")
            .replace("\n", "\n\n")  
        )

        st.markdown("### 💬 Recomendações da IA")
        st.markdown(f"<div style='font-size: 17px; line-height: 1.6'>{resposta_formatada}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Erro ao se comunicar com a API da AI: {e}")