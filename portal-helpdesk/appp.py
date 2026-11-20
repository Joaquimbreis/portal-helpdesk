import streamlit as st
import mysql.connector
import pandas as pd

# ------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------
st.set_page_config(page_title="Portal Web de Helpdesk", layout="wide")

# ------------------------------------------------------
# CONFIGURAÇÃO DE CONEXÃO COM O MYSQL (XAMPP)
# ------------------------------------------------------
CONFIG_BANCO = {
    "host": "localhost",
    "user": "root",
    "password": "",       # No XAMPP, por padrão o usuário root não tem senha
    "database": "helpdesk"
}

# ------------------------------------------------------
# FUNÇÕES DE BANCO DE DADOS
# ------------------------------------------------------

def conectar():
    """Abre uma conexão com o banco de dados MySQL do XAMPP."""
    return mysql.connector.connect(**CONFIG_BANCO)


def criar_tabela():
    """Cria a tabela 'chamados' se ela ainda não existir."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chamados (
            id INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            descricao TEXT NOT NULL,
            prioridade VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()


def inserir_chamado(titulo, descricao, prioridade):
    """Insere um novo chamado no banco, com status inicial 'Aberto'."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chamados (titulo, descricao, prioridade, status) VALUES (%s, %s, %s, %s)",
        (titulo, descricao, prioridade, "Aberto")
    )
    conn.commit()
    cursor.close()
    conn.close()


def buscar_chamados():
    """Busca todos os chamados e devolve como uma tabela (DataFrame)."""
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM chamados ORDER BY id DESC", conn)
    conn.close()
    return df


def atualizar_status(id_chamado, novo_status):
    """Atualiza o status de um chamado específico."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE chamados SET status = %s WHERE id = %s",
        (novo_status, id_chamado)
    )
    conn.commit()
    cursor.close()
    conn.close()


def excluir_chamado(id_chamado):
    """Exclui um chamado do banco de dados."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chamados WHERE id = %s", (id_chamado,))
    conn.commit()
    cursor.close()
    conn.close()


# Garante que a tabela existe antes de qualquer coisa
criar_tabela()

# ------------------------------------------------------
# TÍTULO DA PÁGINA
# ------------------------------------------------------
st.title("🎫 Portal Web de Helpdesk")
st.caption("Sistema de gerenciamento de chamados — Python + Streamlit + MySQL (XAMPP)")

# ------------------------------------------------------
# FORMULÁRIO DE CRIAÇÃO DE CHAMADO
# ------------------------------------------------------
st.subheader("Abrir novo chamado")

with st.form("form_novo_chamado", clear_on_submit=True):
    titulo = st.text_input("Título")
    descricao = st.text_area("Descrição")
    prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta"])

    enviado = st.form_submit_button("Criar chamado")

    if enviado:
        if titulo.strip() == "" or descricao.strip() == "":
            st.error("⚠️ Título e Descrição não podem ficar vazios.")
        else:
            inserir_chamado(titulo.strip(), descricao.strip(), prioridade)
            st.success("✅ Chamado criado com sucesso!")
            st.rerun()

# ------------------------------------------------------
# TABELA DE CHAMADOS (visualizar, editar status, excluir)
# ------------------------------------------------------
st.subheader("Chamados cadastrados")

df = buscar_chamados()

if df.empty:
    st.info("Nenhum chamado cadastrado ainda.")
else:
    tabela_editada = st.data_editor(
        df,
        key="editor_chamados",
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "titulo": st.column_config.TextColumn("Título", disabled=True),
            "descricao": st.column_config.TextColumn("Descrição", disabled=True),
            "prioridade": st.column_config.TextColumn("Prioridade", disabled=True),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["Aberto", "Em andamento", "Resolvido"],
                required=True,
            ),
        },
        hide_index=True,
    )

    if st.button("💾 Salvar alterações no banco de dados"):
        mudancas = st.session_state["editor_chamados"]

        for indice_linha, valores_alterados in mudancas["edited_rows"].items():
            id_chamado = int(df.iloc[indice_linha]["id"])
            if "status" in valores_alterados:
                atualizar_status(id_chamado, valores_alterados["status"])

        for indice_linha in mudancas["deleted_rows"]:
            id_chamado = int(df.iloc[indice_linha]["id"])
            excluir_chamado(id_chamado)

        st.success("✅ Alterações salvas no banco de dados!")
        st.rerun()