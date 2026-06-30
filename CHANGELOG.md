# Changelog

All notable changes to this project will be documented in this file.

## [1.3.0] - 2026-06-30

### Adicionado
- **Tabela e Relação de Lote**: Criação da tabela `Lote` (`loteID`, `descricao`) no banco SQLite e inclusão da propriedade `lote` nas tabelas `Linha` e `LinhaExcluida`.
- **Gestão de Lotes**: CRUD para cadastro, listagem e exclusão de Lotes no painel de Tabelas de Referência (`mod_cadastro_ref.py`).
- **Seleção de Lote**: Dropdowns de Lote adicionados nos formulários de cadastro e edição de linha.
- **Detalhes Automáticos do Operador**: O preenchimento do operador na linha agora carrega e exibe automaticamente o `Termo`, `Razão Social` e `Nome Fantasia` vinculados na Ficha Cadastral da linha.
- **Propulsão Multiseleção**: Campo de Propulsão reconfigurado como multiselect (igual aos Dias de Operação), permitindo associar múltiplos tipos de propulsão a uma única linha, salvando-os de forma concatenada no banco de dados e adaptando as consultas via filtro (`LIKE`).

### Modificado / Ajustado
- **Remoção do Grupamento BRS**: Omissão das referências visuais de "Grupamento BRS" das telas de cadastro, edição, consulta e ficha cadastral (com a tabela preservada internamente no BD).
- **Layout da Ficha Cadastral**:
  - Reordenação de campos em *Informações Gerais* (GTFS agora precede a Extensão de volta).
  - Distribuição em duas colunas na seção *Operador Responsável* (Coluna 1: Razão Social, Lote e Área Operacional; Coluna 2: Nome Fantasia e Termo).
  - Alteração na Área Operacional para juntar `codigo` e `descricao` (e não mais `corReferencia`), enquanto o fundo colorido é mantido dinâmico.
  - Correção de CSS no badge da Área Operacional para respeitar o casing original do banco (remoção de `text-transform: lowercase`).

## [1.2.0] - 2026-06-26

### Adicionado
- **Página de Rosto**: Interface inicial redesenhada no estilo split-screen com opção de Acesso Público direto (visitante) e Acesso Interno restrito para usuários cadastrados.
- **Módulo GTFS**: Upload e exclusão de arquivos de dados geográficos do GTFS (`.zip`) salvos em disco diretamente via interface (apenas admin/editor).
- **Tipo de Propulsão**: Campo de propulsão (Diesel, Elétrico, GNV, Híbrido, etc.) integrado ao banco de dados e formulários de cadastro, edição, visualização e tabelas de referência.
- **Filtros Avançados**: Filtros de status do GTFS e assunto do último ofício no painel de consultas.
- **Cores por Área**: Identificação por cores correspondentes às áreas operacionais (ex: Internorte, Intersul, Santa Cruz, Transcarioca) aplicadas de forma visual nas fichas cadastrais.

### Modificado
- Reformatação de tabelas e documentação técnica no `README.md`, `AGENTS.md` e `RELEASE.md`.

---

## [1.1.0] - 2026-05-08

### Adicionado
- **Padrão MVC**: Reorganização completa da estrutura de arquivos em módulos (`models/`, `views/` e `utils/`).
- **Histórico de Linhas**: Implementação de trilha de auditoria completa (`LogEventos`) para registrar Criação, Alteração e Exclusão.
- **Tabela de Exclusão**: Implementação da tabela `LinhaExcluida` com campos obrigatórios de justificativa/ofício de exclusão.
- **Acesso Público**: Rota de acesso visitante sem credenciais (modo consulta básica).
- **Gerenciamento de Tabelas**: Edição e cadastro de tabelas de referência secundárias (serviços, operadores, áreas operacionais, etc.).
- **Visualizador Geográfico**: Carregamento e renderização de itinerários no mapa utilizando dados geográficos do GTFS.

### Corrigido
- Ajustes de caminhos de banco, imports e correções de layout responsivo no Streamlit.
- Correção de dependências e arquivos de build.

---

## [1.0.0] - 2026-04-20

### Adicionado
- Estrutura inicial do projeto com Streamlit.
- Banco de dados SQLite (`database_RIO.db`) contendo o cadastro base de linhas e tabelas auxiliares.
- Sistema de controle de acesso integrado com quatro tipos de usuário (admin, editor, visualizador, user).
- Utilitários de inicialização de banco e população de dados de teste.
- Script de inicialização automática no Windows (`iniciar_sistema.bat`).
