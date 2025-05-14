import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase
from openai import OpenAI

# === CONFIGURAÇÕES GERAIS ===
st.set_page_config(page_title="Dashboard Financeiro", layout="wide")
st.title("📊 Dashboard Financeiro Pessoal")

# ==== CONFIGURAÇÃO FIREBASE AUTH ====
firebaseConfig = {
    "apiKey": st.secrets["firebase"]["apiKey"],
    "authDomain": st.secrets["firebase"]["authDomain"],
    "projectId": st.secrets["firebase"]["project_id"],
    "storageBucket": st.secrets["firebase"]["storageBucket"],
    "messagingSenderId": st.secrets["firebase"]["messagingSenderId"],
    "appId": st.secrets["firebase"]["appId"],
    "measurementId": st.secrets["firebase"]["measurementId"],
    "databaseURL": ""
}
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# ==== LOGIN / CADASTRO ====
if "user" not in st.session_state:
    st.subheader("🔐 Login ou Cadastro")
    choice = st.selectbox("Escolha", ["Login", "Cadastro"])

    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")

    if choice == "Cadastro":
        if st.button("Criar conta"):
            try:
                user = auth.create_user_with_email_and_password(email, password)
                st.session_state.user = user
                st.session_state.uid = user["localId"]
                st.success("Conta criada com sucesso!")
            except Exception as e:
                st.error(f"Erro: {e}")
    elif choice == "Login":
        if st.button("Entrar"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user = user
                st.session_state.uid = user["localId"]
                st.success("Logado com sucesso!")
            except Exception as e:
                st.error("Login inválido")

# ==== APÓS LOGIN ====
if "user" in st.session_state:
    uid = st.session_state["uid"]

    # === INICIALIZAÇÃO FIREBASE ===
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'),
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
            "universe_domain": st.secrets["firebase"]["universe_domain"]
        })
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    st.subheader("📂 Subir Excel Antigo")
    uploaded_file = st.file_uploader("Envie seu Excel antigo com abas: entrada, saida, investimento", type="xlsx")
    if uploaded_file:
        df_entrada = pd.read_excel(uploaded_file, sheet_name="entrada")
        df_saida = pd.read_excel(uploaded_file, sheet_name="saida")
        df_invest = pd.read_excel(uploaded_file, sheet_name="investimento")

        def upload_df(df, aba):
            for _, row in df.iterrows():
                doc = row.to_dict()
                doc["data_upload"] = datetime.now()
                db.collection(f"{aba}").add({**doc, "uid": uid})

        upload_df(df_entrada, "entrada")
        upload_df(df_saida, "saida")
        upload_df(df_invest, "investimento")
        st.success("Dados salvos com sucesso no Firebase!")

    # === CLIENTE OPENAI ===
    client = OpenAI(
        api_key=st.secrets["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1"
    )

    # === FUNÇÃO PARA BUSCAR DADOS DO FIRESTORE ===
    @st.cache_data
    def carregar_dados(uid):
        def fetch_collection(colecao):
            docs = db.collection(colecao).where("uid", "==", uid).stream()
            data = [doc.to_dict() for doc in docs]
            return pd.DataFrame(data)

        entrada = fetch_collection("entrada")
        saida = fetch_collection("saida")
        investimento = fetch_collection("investimento")
        return entrada, saida, investimento

    entrada_df, saida_df, investimento_df = carregar_dados(uid)

    opcao = st.radio("🔎 Visualizar:", ["Histórico completo", "Mês atual"])
    if opcao == "Mês atual":
        entrada_df = entrada_df.tail(1)
        saida_df = saida_df.tail(1)
        investimento_df = investimento_df.tail(1)

    tabs = st.tabs(["💰 Entradas", "💸 Saídas", "📈 Investimentos", "📖 Feedback Matemático", "🤖 Feedback Personalizado", "💻 Consulte a IA"])
# === ENTRADAS ===
with tabs[0]:
    st.header("💰 Análise de Entradas")
    if not entrada_df.empty:
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
    else:
        st.info("Nenhuma entrada encontrada.")

# === SAÍDAS ===
with tabs[1]:
    st.header("💸 Análise de Saídas")
    if not saida_df.empty:
        saida_df["Total Gastos"] = saida_df.drop(columns="Mês").select_dtypes(include="number").sum(axis=1)

        st.subheader("📆 Gastos Totais por Mês")
        fig_gastos = px.line(saida_df, x="Mês", y="Total Gastos", markers=True, text="Total Gastos")
        fig_gastos.update_traces(textposition="top center")
        st.plotly_chart(fig_gastos, use_container_width=True)

        st.subheader("📋 Gastos por Categoria")
        categorias = saida_df.drop(columns=["Mês", "Total Gastos"], errors="ignore")
        fig_cat2 = px.bar(saida_df, x="Mês", y=categorias.columns, barmode="group", text_auto=True)
        fig_cat2.update_traces(textposition="outside")
        st.plotly_chart(fig_cat2, use_container_width=True)

        st.subheader("📊 Distribuição Média de Gastos")
        media_gastos = categorias.mean()
        fig2, ax2 = plt.subplots()
        ax2.pie(media_gastos, labels=media_gastos.index, autopct='%1.1f%%', startangle=90)
        ax2.axis('equal')
        st.pyplot(fig2)
    else:
        st.info("Nenhuma saída encontrada.")

# === INVESTIMENTOS ===
with tabs[2]:
    st.header("📈 Análise de Investimentos e Crescimento")
    if not investimento_df.empty:
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
    else:
        st.info("Nenhum investimento encontrado.")
# === FEEDBACK MATEMÁTICO ===
with tabs[3]:
    st.header("🔍 Análise e Recomendações")
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

# === FEEDBACK IA e CONSULTA IA ===
with tabs[4]:
    st.header("🤖 Feedback Personalizado (em construção)")
    st.info("Essa seção será alimentada com IA futuramente.")

with tabs[5]:
    st.header("💻 Consulte a IA")
    pergunta = st.text_input("Digite uma pergunta sobre suas finanças:")
    if pergunta:
        resposta = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": pergunta}]
        )
        st.write(resposta.choices[0].message.content)
