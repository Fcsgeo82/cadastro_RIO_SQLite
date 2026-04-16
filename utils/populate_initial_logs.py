"""
populate_initial_logs.py
Popula o histórico de eventos (LogEventos) com base nos dados existentes.
- Limpa logs de migração anteriores antes de reinserir para evitar duplicatas.
- Busca os oficioIDs corretos de cada evento.
- Não duplica eventos que já foram registrados pelos processos reais.
"""

import sqlite3
import os
import uuid
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_NAME = os.path.join(BASE_DIR, "database_RIO.db")


def populate_initial_logs():
    """Popula o histórico de eventos baseado nos dados existentes."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("Limpando logs de migração anteriores...")
    cursor.execute("DELETE FROM LogEventos WHERE detalhes LIKE 'Migração automática%'")
    removidos = cursor.rowcount
    print(f"  {removidos} logs de migração removidos.")

    eventos_criados = 0

    # ------------------------------------------------------------------
    # 1. Linhas ativas (tabela Linha)
    # ------------------------------------------------------------------
    cursor.execute("""
        SELECT linhaID, numeroLinha, dataCadastro, ultimaAtualizacao,
               oficio, oficioprimeiroHistorico, oficioUltimaAlteracao
        FROM Linha
    """)
    linhas = cursor.fetchall()

    for row in linhas:
        linha_id, numero, data_cadastro, ultima_alt, oficio, of_primeiro, of_ult_alt = row

        # Criação — usa oficioprimeiroHistorico ou oficio como fallback
        oficio_criacao = of_primeiro or oficio
        log_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT OR IGNORE INTO LogEventos
                (logID, linhaID, numeroLinha, tipoEvento, dataEvento, usuario, oficioID, detalhes)
            VALUES (?, ?, ?, 'Criação', ?, 'sistema', ?, 'Migração automática')
        """, (log_id, linha_id, numero, data_cadastro, oficio_criacao))
        eventos_criados += cursor.rowcount

        # Alteração — só se a data de atualização for posterior à criação
        if ultima_alt and data_cadastro:
            try:
                dt_alt = datetime.fromisoformat(ultima_alt.replace('Z', '+00:00'))
                dt_cria = datetime.fromisoformat(data_cadastro.replace('Z', '+00:00'))
                if dt_alt > dt_cria:
                    oficio_alt = of_ult_alt or oficio
                    log_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT OR IGNORE INTO LogEventos
                            (logID, linhaID, numeroLinha, tipoEvento, dataEvento, usuario, oficioID, detalhes)
                        VALUES (?, ?, ?, 'Alteração', ?, 'sistema', ?, 'Migração automática - última atualização')
                    """, (log_id, linha_id, numero, ultima_alt, oficio_alt))
                    eventos_criados += cursor.rowcount
            except Exception as e:
                print(f"  Aviso ao processar alteração de {numero}: {e}")

    print(f"  Linhas ativas processadas: {len(linhas)}")

    # ------------------------------------------------------------------
    # 2. Linhas excluídas (tabela LinhaExcluida)
    # ------------------------------------------------------------------
    cursor.execute("""
        SELECT linhaID, numeroLinha, dataCadastro, ultimaAtualizacao,
               dataExclusao, usuarioExclusao,
               oficio, oficioprimeiroHistorico, oficioUltimaAlteracao, oficioExclusao
        FROM LinhaExcluida
    """)
    linhas_excluidas = cursor.fetchall()

    for row in linhas_excluidas:
        (linha_id, numero, data_cadastro, ultima_alt,
         data_exclusao, usuario_excl,
         oficio, of_primeiro, of_ult_alt, of_exclusao) = row

        usuario_excl = usuario_excl or 'sistema'

        # Criação
        if data_cadastro:
            oficio_criacao = of_primeiro or oficio
            log_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT OR IGNORE INTO LogEventos
                    (logID, linhaID, numeroLinha, tipoEvento, dataEvento, usuario, oficioID, detalhes)
                VALUES (?, ?, ?, 'Criação', ?, ?, ?, 'Migração automática')
            """, (log_id, linha_id, numero, data_cadastro, usuario_excl, oficio_criacao))
            eventos_criados += cursor.rowcount

        # Alteração
        if ultima_alt and data_cadastro:
            try:
                dt_alt = datetime.fromisoformat(ultima_alt.replace('Z', '+00:00'))
                dt_cria = datetime.fromisoformat(data_cadastro.replace('Z', '+00:00'))
                if dt_alt > dt_cria:
                    oficio_alt = of_ult_alt or oficio
                    log_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT OR IGNORE INTO LogEventos
                            (logID, linhaID, numeroLinha, tipoEvento, dataEvento, usuario, oficioID, detalhes)
                        VALUES (?, ?, ?, 'Alteração', ?, ?, ?, 'Migração automática')
                    """, (log_id, linha_id, numero, ultima_alt, usuario_excl, oficio_alt))
                    eventos_criados += cursor.rowcount
            except Exception as e:
                print(f"  Aviso ao processar alteração de excluída {numero}: {e}")

        # Exclusão
        if data_exclusao:
            log_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT OR IGNORE INTO LogEventos
                    (logID, linhaID, numeroLinha, tipoEvento, dataEvento, usuario, oficioID, detalhes)
                VALUES (?, ?, ?, 'Exclusão', ?, ?, ?, 'Migração automática')
            """, (log_id, linha_id, numero, data_exclusao, usuario_excl, of_exclusao))
            eventos_criados += cursor.rowcount

    print(f"  Linhas excluídas processadas: {len(linhas_excluidas)}")

    conn.commit()
    conn.close()

    print("-" * 40)
    print(f"Concluído! {eventos_criados} eventos criados.")


if __name__ == "__main__":
    populate_initial_logs()