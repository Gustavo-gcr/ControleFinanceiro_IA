import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import openai

# === CONFIGURAÇÕES ===
sns.set(style="whitegrid")
st.set_page_config(page_title="Dashboard Financeiro", layout="wide")
st.title("📊 Dashboard Financeiro Pessoal")

# === CONFIGURAR CHAVE DA API ===
openai.api_key = st.secrets["openai"]["api_key"]

# === UPLOAD ===
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

    tabs = st.tabs(["💰 Entradas", "💸 Saídas", "📈 Investimentos", "🤖 Feedback Inteligente"])

    # === ABA 1: ENTRADAS ===
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

    # === ABA 2: SAÍDAS ===
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

    # === ABA 3: INVESTIMENTOS ===
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
        fig_bar.add_trace(go.Bar(x=comparativo["Mês"], y=comparativo["Gastos"], name="Gastos", marker_color="indianred"))
        fig_bar.add_trace(go.Bar(x=comparativo["Mês"], y=comparativo["Investimentos"], name="Investimentos", marker_color="seagreen"))
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
        projecao_df["Texto"] = projecao_df["Saldo Projetado"].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        fig_proj = px.line(projecao_df, x="Mês", y="Saldo Projetado", markers=True, text="Texto")
        fig_proj.update_traces(textposition="top center")
        st.plotly_chart(fig_proj, use_container_width=True)

    # === ABA 4: FEEDBACK PERSONALIZADO COM IA ===
    with tabs[3]:
        st.header("🤖 Feedback Inteligente com IA")

        st.markdown("📄 Gerando análise personalizada dos seus dados financeiros...")

        # Gerar prompt com resumo dos dados
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

        # Chamada à OpenAI
        resposta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um especialista em finanças pessoais."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        # Exibe a resposta da IA
        st.markdown("### 💬 Recomendações da IA")
        st.write(resposta["choices"][0]["message"]["content"])
