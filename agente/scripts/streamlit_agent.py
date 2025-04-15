import streamlit as st
import mysql.connector
import openai
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração inicial
st.set_page_config(page_title="dioBank Consultas", page_icon="🏛️")
st.title("🏛️ dioBank Consultas")

# Sidebar para credenciais
st.sidebar.header("🔐 Configurações")
openai_api_key = st.sidebar.text_input("Chave da API OpenAI", type="password")
mysql_host = st.sidebar.text_input("MySQL Host", value="localhost")
mysql_user = st.sidebar.text_input("Usuário MySQL", value="root")
mysql_password = st.sidebar.text_input("Senha MySQL", type="password")
mysql_db = st.sidebar.text_input("Nome do Banco de Dados", value="dioBank")

# Sessão para manter pergunta sugerida
if "pergunta" not in st.session_state:
    st.session_state.pergunta = ""

# Sugestões de perguntas como no GPT
st.markdown("### 💬 Sugestões de perguntas")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("📋 Clientes"):
        st.session_state.pergunta = "Me mostre todos os clientes"
with col2:
    if st.button("💸 Pagamentos"):
        st.session_state.pergunta = "Me mostre todos os pagamentos"
with col3:
    if st.button("🏠 Endereços"):
        st.session_state.pergunta = "Me mostre todos os endereços"
with col4:
    if st.button("📈 Movimentações"):
        st.session_state.pergunta = "Me mostre todas as movimentações"

# Campo de pergunta
st.markdown("### ✍️ Pergunta personalizada")
pergunta = st.text_input("Digite sua pergunta em linguagem natural:", 
                         value=st.session_state.pergunta, 
                         key="input_pergunta")

# Função para obter estrutura das tabelas
def obter_estruturas_tabelas():
    try:
        conn = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_db
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tabelas = cursor.fetchall()

        colunas = {}
        for tabela in tabelas:
            cursor.execute(f"DESCRIBE {tabela[0]};")
            colunas_tabela = cursor.fetchall()
            colunas[tabela[0]] = [coluna[0] for coluna in colunas_tabela]

        cursor.close()
        conn.close()
        return colunas
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return {}

# Função para gerar query
def gerar_query_sql(pergunta, colunas):
    openai.api_key = openai_api_key
    prompt = f"""
Você é um assistente de SQL que opera para o banco de dados fictício chamado Dio Bank.
Você deve gerar queries baseadas na seguinte estrutura do banco de dados:
{colunas}

Pergunta: {pergunta}
Resposta em SQL:
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Você é um assistente de SQL."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0
    )
    query = response['choices'][0]['message']['content'].strip()
    return query.replace("```sql", "").replace("```", "").strip()

# Função para executar a query
def executar_query(query):
    try:
        conn = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_db
        )
        cursor = conn.cursor()
        cursor.execute(query)
        resultados = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        return colunas, resultados
    except Exception as e:
        st.error(f"Erro ao executar a query: {e}")
        return [], []

# Execução principal
if pergunta:
    st.info("🔍 Gerando SQL com base na pergunta...")
    estrutura = obter_estruturas_tabelas()
    if estrutura:
        query = gerar_query_sql(pergunta, estrutura)
        st.code(query, language="sql")
        colunas, resultados = executar_query(query)

        if resultados:
            st.success("✅ Consulta realizada com sucesso!")
            st.dataframe([dict(zip(colunas, row)) for row in resultados])
        else:
            st.warning("Nenhum resultado encontrado.")
