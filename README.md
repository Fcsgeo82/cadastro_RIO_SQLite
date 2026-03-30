# 🚌 Sistema de Cadastro de Linhas - RIO Cadastro

Aplicação Streamlit para cadastro e consulta de linhas de ônibus utilizando banco de dados local **SQLite**.

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.10+

### Instalação

1. **Criar e ativar ambiente virtual:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Inicializar o Banco de Dados:**
   Este passo cria as tabelas e popula com dados iniciais (Serviços, Operadores, Áreas, etc).
   ```bash
   python init_db.py
   ```

### Executar a Aplicação

```bash
streamlit run app.py
```

Acesse em: http://localhost:8501

## 📁 Estrutura de Pastas

```
cadastro_RIO_SQLite/
├── app.py                 # Aplicação principal Streamlit
├── config.py              # Conexão com SQLite
├── db.py                  # Operações de Banco de Dados (CRUD)
├── init_db.py             # Script de inicialização e seed do banco
├── database_RIO.db       # Banco de dados SQLite (gerado após init_db)
├── mod_cadastro.py        # Módulo UI: Cadastro de linhas
├── mod_consulta.py        # Módulo UI: Consulta de linhas
├── mod_cadastro_ref.py    # Módulo UI: Cadastro de tabelas de ref
├── Schema.csv             # Definição do esquema das tabelas
├── requirements.txt       # Dependências Python
└── README.md              # Este arquivo
```

## ⚙️ Funcionalidades

- ✅ **Cadastro de Linhas** - Adicionar novos registros de ônibus
- ✅ **Consulta com Filtros** - Busca por número, área, operador e tipo
- ✅ **Tabelas de Referência** - Gerenciamento dinâmico de serviços, áreas e operadores
- ✅ **Exportação CSV** - Download dos resultados da consulta
- ✅ **Operação Local** - 100% offline, sem dependência de nuvem

## 🛠️ Desenvolvimento

### Adicionar nova tabela
1. Adicione a definição no `Schema.csv`
2. Atualize o `init_db.py` com dados iniciais se necessário
3. Crie o formulário em `mod_cadastro_ref.py`

### Modificar Consultas
- Edite as funções no `db.py`. O projeto utiliza a biblioteca padrão `sqlite3` e `pandas` para retornar DataFrames.

## 📝 Notas Importantes

- 🔒 O banco de dados `database_RIO.db` é local. Faça backups periódicos se houver dados críticos.
- 🧹 Para limpar o banco e recomeçar do zero, apague o arquivo `.db` e rode `python init_db.py`.

## 🐛 Troubleshooting

**Módulo não encontrado:**
```bash
pip install -r requirements.txt
```

**Erro ao atualizar o banco (Locked):**
Certifique-se de que o App Streamlit ou outro visualizador de SQLite (DB Browser) não está mantendo a conexão aberta durante operações de escrita críticas.
