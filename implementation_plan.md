# Plano: Ações na Consulta de Linhas

Adicionar funcionalidades de consulta de histórico, edição e exclusão de linhas diretamente da tela de consulta.

## Mudanças Propostas

### Infraestrutura de Dados

#### [MODIFY] [Schema.csv](file:///c:/github_repositories/cadastro_RIO_SQLite/Schema.csv)
- [NEW] Adicionar tabela `LogAlteracao` para rastrear mudanças.
  - Campos: `logID`, [tabela](file:///c:/github_repositories/cadastro_RIO_SQLite/db.py#26-29), `registroID`, `acao` (CRIAR, ALTERAR, EXCLUIR), `dados_anteriores`, `dados_novos`, `data`, `usuario`.

#### [MODIFY] [init_db.py](file:///c:/github_repositories/cadastro_RIO_SQLite/init_db.py)
- Garantir a criação da nova tabela de logs.

### Acesso a Dados

#### [MODIFY] [db.py](file:///c:/github_repositories/cadastro_RIO_SQLite/db.py)
- Modificar [inserir_linha](file:///c:/github_repositories/cadastro_RIO_SQLite/db.py#151-200) para registrar log.
- [NEW] `atualizar_linha(linhaID, novos_dados)`: Atualiza registro e registra log.
- [NEW] `excluir_linha(linhaID, dados_exclusao)`: Insere em `exclusaoLinha`, remove/inativa em `Linha` e registra log.
- [NEW] `consultar_historico(linhaID)`: Retorna DataFrame com os logs da linha.
- [NEW] `buscar_linha_por_id(linhaID)`: Retorna os dados atuais para preenchimento do form.

### Interface do Usuário

#### [MODIFY] [mod_cadastro.py](file:///c:/github_repositories/cadastro_RIO_SQLite/mod_cadastro.py)
- Refatorar a função [render](file:///c:/github_repositories/cadastro_RIO_SQLite/mod_cadastro_ref.py#350-378) para aceitar `linha_existente_id`. Se presente, carregar dados e mudar botão para "Salvar Alterações".

#### [MODIFY] [mod_consulta.py](file:///c:/github_repositories/cadastro_RIO_SQLite/mod_consulta.py)
- Implementar seleção de linha no dataframe.
- Mostrar botões de ação ("📜 Histórico", "✏️ Alterar", "🗑️ Excluir") para a linha selecionada.
- Usar `st.dialog` (ou modais) para as telas de Histórico e Excluir.

## Plano de Verificação

### Testes Automatizados
- Script `test_actions.py` para validar o fluxo de Log -> Update -> Log.

### Verificação Manual
- Realizar uma busca, selecionar uma linha e testar cada uma das três ações.
- Verificar se a aba "Histórico" reflete exatamente as mudanças feitas na aba "Alterar".
