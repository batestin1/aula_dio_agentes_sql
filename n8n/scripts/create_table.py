import pandas as pd
import unicodedata
import re
from sqlalchemy import create_engine, text

# === Função para normalizar nomes das colunas ===
def normalizar_colunas(df):
    colunas_novas = []
    for col in df.columns:
        # Remove acentos
        col = unicodedata.normalize('NFKD', col).encode('ASCII', 'ignore').decode('utf-8')
        # Converte para minúsculas
        col = col.lower()
        # Substitui espaços por underscore
        col = col.replace(' ', '_')
        # Remove caracteres especiais
        col = re.sub(r'[^a-zA-Z0-9_]', '', col)
        colunas_novas.append(col)
    df.columns = colunas_novas
    return df

# === Configurações de conexão ===
user = 'root'
password = 'admin123'
host = 'localhost'
port = '3306'
schema = 'despesasViagem'

# === Caminhos dos arquivos CSV ===
path_pag = 'datasets/2024_20250309_Viagens/2024_Pagamento.csv'
path_passag = 'datasets/2024_20250309_Viagens/2024_Passagem.csv'
path_trecho = 'datasets/2024_20250309_Viagens/2024_Trecho.csv'
path_viagem = 'datasets/2024_20250309_Viagens/2024_Viagem.csv'

print("Lendo arquivos CSV...")

pagmento = pd.read_csv(path_pag, encoding='latin1', sep=';')
passageiro = pd.read_csv(path_passag, encoding='latin1', sep=';')
trecho = pd.read_csv(path_trecho, encoding='latin1', sep=';')
viagem = pd.read_csv(path_viagem, encoding='latin1', sep=';')

# === Normaliza os nomes das colunas ===
lista_table = [pagmento, passageiro, trecho, viagem]
nomes_tabelas = ['pagamento', 'passageiro', 'trecho', 'viagem']

for i in range(len(lista_table)):
    lista_table[i] = normalizar_colunas(lista_table[i])

# === Conectando ao MySQL e criando banco ===
print("Conectando ao MySQL...")
engine_root = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}:{port}')

with engine_root.connect() as conn:
    print(f"Criando o banco de dados {schema} (se não existir)...")
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {schema};"))

# === Conectar agora já no schema ===
print(f"Conectando ao banco de dados {schema}...")
engine_enem = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{schema}')

# === Enviar os DataFrames para o banco ===
for nome, tabela in zip(nomes_tabelas, lista_table):
    try:
        tabela.to_sql(
            name=nome,
            con=engine_enem,
            if_exists='replace',
            index=False,
            chunksize=1000  # Envia 1000 linhas por vez
        )
        print(f"Tabela '{nome}' inserida com sucesso!")
    except Exception as e:
        print(f"Erro ao inserir a tabela '{nome}': {e}")

print("Tabelas inseridas com sucesso!")

# === Mostrar os nomes das tabelas no banco ===
print("\nTabelas criadas no banco de dados:")
with engine_enem.connect() as conn:
    resultado = conn.execute(text("SHOW TABLES;"))
    tabelas = [linha[0] for linha in resultado]
    for nome in tabelas:
        print(f"- {nome}")
