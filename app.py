import streamlit as st
import pandas as pd
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase

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
st.title("Login ou Cadastro")
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
    st.subheader("📂 Subir Excel Antigo")
    uploaded_file = st.file_uploader("Envie seu Excel antigo com abas: entrada, saida, investimento", type="xlsx")
    if uploaded_file:
        df_entrada = pd.read_excel(uploaded_file, sheet_name="entrada")
        df_saida = pd.read_excel(uploaded_file, sheet_name="saida")
        df_invest = pd.read_excel(uploaded_file, sheet_name="investimento")

        # Firebase Admin
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
        uid = st.session_state.user["localId"]

        # Subir os dados
        def upload_df(df, aba):
            for _, row in df.iterrows():
                doc = row.to_dict()
                doc["data_upload"] = datetime.now()
                db.collection(f"{aba}").add({**doc, "user_id": uid})

        upload_df(df_entrada, "entrada")
        upload_df(df_saida, "saida")
        upload_df(df_invest, "investimento")
        st.success("Dados salvos com sucesso no Firebase!")
