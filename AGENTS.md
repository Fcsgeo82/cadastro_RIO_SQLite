# AGENTS.md

## Quick Start

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Initialize database (required on first run)
python utils/init_db.py

# Run the app
streamlit run app.py
```

## Architecture

- **Entry point**: `app.py` (Streamlit)
- **Database**: SQLite at `database_RIO.db`
- **MVC structure**:
  - `models/db.py` — DB operations, auth, reference loaders
  - `models/config.py` — SQLite connection
  - `views/` — UI modules (mod_consulta, mod_cadastro, etc.)

## Default Users

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Full access |
| editor | editor123 | Consult, Cadastro, Tabelas Ref, Linhas Excluídas |
| visualizador | vis123 | Consult only (with all filters) |
| user | user123 | Consult only (restricted filters) |

## Database

- SQLite at `database_RIO.db` (root level)
- Tables: Linha, LinhaExcluida, Itinerario, Servico, Operador, AreaOperacional, TipoSistema, Parametro, Caracteristica, GrupamentoBRS, TipoVeiculo, Oficio, Usuarios, LogEventos

## Key Commands

- `python utils/init_db.py` — Create tables and seed initial data
- `python utils/init_db_dados_fake.py` — Populate with test data (optional)
- `python utils/populate_initial_logs.py` — Backfill history from existing data (run once after adding LogEventos). Não é necessário no primeiro uso de um projeto novo, só é útil se o projeto já tiver dados e foi adicionado o LogEventos posteriormente.  

## Features

- **History Tracking**: Full audit trail (Criação, Alteração, Exclusão) via LogEventos table
- Aba "Linhas Excluídas" renamed to "📜 Histórico de Linhas" with filters
- Automatic logging on create/update/delete operations