from crewai_tools import BaseTool
from typing import Any

class SchemaExplorerTool(BaseTool):
    name = "Schema Explorer"
    description = "Explora o schema de um banco de dados MySQL e retorna as tabelas e colunas."

    def _run(self, query: Any) -> str:
        import mysql.connector
        host = query.get("host")
        user = query.get("user")
        password = query.get("password")
        database = query.get("database")

        try:
            conn = mysql.connector.connect(
                host=host, user=user, password=password, database=database
            )
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tabelas = cursor.fetchall()

            schema_info = "🔍 **Schema do Banco de Dados**\n"
            for tabela in tabelas:
                tabela_nome = tabela[0]
                cursor.execute(f"DESCRIBE {tabela_nome}")
                colunas = cursor.fetchall()
                schema_info += f"\n📦 **Tabela: `{tabela_nome}`**\n"
                for col in colunas:
                    schema_info += f"   - 🔸 `{col[0]}`: *{col[1]}*\n"

            return schema_info
        except Exception as e:
            return f"🚨 Erro ao acessar schema do banco: {e}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
