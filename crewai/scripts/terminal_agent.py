from crewai import Agent, Task, Crew
import mysql.connector
import json
import os
import sys
import os

# Adiciona o diretório pai ao path para que 'scripts' seja reconhecido
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.schemaExplorerTool import SchemaExplorerTool



# Função para criar agente com a ferramenta de schema
def criar_agente_com_tool():
    return Agent(
        name="ConsultorSQL",
        role="Especialista em SQL com acesso ao schema do banco",
        goal="Gerar SQL com base no schema real do banco",
        backstory="Agente treinado para compreender o banco de dados e responder perguntas com SQL baseado no contexto real.",
        tools=[SchemaExplorerTool()],
        verbose=True,
        allow_delegation=False
    )

# Carregando variáveis do JSON
with open("crewai/parametros/arquivo.json", "r") as file:
    var = json.load(file)

host = var['host']
user = var['user']
password = var['password']
database = var['schema']
port = var['port']
os.environ["OPENAI_API_KEY"] = var['api_key']

# Função para conectar ao MySQL
def conectar_mysql(host, user, password, database):
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

# Função para executar consulta
def executar_consulta(conexao, query):
    cursor = conexao.cursor()
    cursor.execute(query)
    resultado = cursor.fetchall()
    colunas = [desc[0] for desc in cursor.description]
    cursor.close()
    return colunas, resultado

# Execução principal
if __name__ == "__main__":
    print("🚀 Agente IA para consultas SQL via Terminal")

    conexao = conectar_mysql(host, user, password, database)
    agente = criar_agente_com_tool()

    while True:
        pergunta = input("\nDigite sua pergunta (ou 'sair'): ")
        if pergunta.lower() == 'sair':
            break

        task = Task(
            description=f"Converter a pergunta '{pergunta}' para uma consulta SQL válida em MySQL",
            expected_output="Analisar a consulta, entrar no banco de dados e retornar uma resposta válida em formato de texto.",
            agent=agente
        )

        crew = Crew(
            agents=[agente],
            tasks=[task],
            verbose=True
        )

        resposta = crew.kickoff(
            tools_input={"host": host, "user": user, "password": password, "database": database}
        )

        # ✅ Aqui extraímos o texto da query a partir da resposta do Crew
        query_sql = resposta.output if hasattr(resposta, 'output') else str(resposta)
        print("\nQuery sugerida:", query_sql)

        try:
            colunas, resultado = executar_consulta(conexao, query_sql)
            print("\nResultado:")
            print(colunas)
            for linha in resultado:
                print(linha)
        except Exception as e:
            print("❌ Erro ao executar query:", e)
