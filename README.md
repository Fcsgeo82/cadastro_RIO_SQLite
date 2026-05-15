# 🚌 Sistema de Cadastro de Linhas - RIO Cadastro

Aplicação Streamlit para cadastro e consulta de linhas de ônibus utilizando banco de dados local **SQLite** com sistema de autenticação.

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

### Inicializar o Banco de Dados
Este passo cria as tabelas e popula com dados iniciais (Serviços, Operadores, Áreas, etc).
```bash
python utils/init_db.py
```

*(Opcional)* Se o banco já possui dados e você acabou de adicionar a funcionalidade de logs:
```bash
python utils/populate_initial_logs.py
```

### Executar a Aplicação

```bash
streamlit run app.py
ou
python -m streamlit run app.py #Caso o streamlit não esteja no path.
```

Acesse em: http://localhost:8501

## 🔐 Login e Autenticação

O sistema possui 4 tipos de usuários com permissões diferentes:

| Usuário | Senha | Permissões |
|---------|-------|------------|
| **admin** | admin123 | Full Access (Consulta, Cadastro, Tabelas Ref, Usuários, Histórico, GTFS) |
| **editor** | editor123 | Consult, Cadastro, Tabelas Ref, Histórico |
| **visualizador** | vis123 | Apenas Consulta (com todos os filtros) e Tabelas Ref |
| **user** | user123 | Apenas Consulta (filtros restritos) |

> ⚠️ As senhas iniciais devem ser alteradas após a primeira utilização. Mínimo 8 caracteres, 1 maiúscula, 1 número, 1 símbolo.

### Políticas de Segurança

- **Rate Limiting**: Após 5 tentativas incorretas, a conta é bloqueada por 15 minutos
- **Validação de Senha**: Mínimo 8 caracteres, 1 letra maiúscula, 1 número, 1 símbolo especial

## 📁 Estrutura de Pastas (Padrão MVC)

```
cadastro_RIO_SQLite/
├── app.py                      # Aplicação principal Streamlit (Entry Point)
├── models/                     # Model - Dados e lógica de banco
│   ├── db.py                   # Operações de Banco de Dados (CRUD + Auth)
│   └── config.py               # Conexão com SQLite
├── views/                      # View - Interface Streamlit
│   ├── mod_consulta.py         # Módulo UI: Consulta de linhas
│   ├── mod_cadastro.py         # Módulo UI: Cadastro de linhas
│   ├── mod_edicao.py           # Módulo UI: Edição completa de registros
│   ├── mod_ficha.py            # Módulo UI: Ficha cadastral detalhada
│   ├── mod_historico.py        # Módulo UI: Histórico e rastreamento de revisões
│   ├── mod_usuarios.py         # Módulo UI: Gerenciamento de usuários (apenas admin)
│   ├── mod_cadastro_ref.py     # Módulo UI: Cadastro de tabelas de referência
│   └── mod_gtfs.py             # Módulo UI: Processamento de dados GTFS
├── utils/                      # Utilitários
│   ├── init_db.py              # Script de inicialização do banco de dados
│   ├── init_db_dados_fake.py   # Script para dados de teste
│   ├── populate_initial_logs.py # Backfill de histórico para dados existentes
│   └── ui_components.py        # Componentes visuais reutilizáveis
├── database_RIO.db            # Banco de dados SQLite (gerado após init_db)
├── Schema.csv                  # Definição do esquema das tabelas
├── Schema BQ - TABELAS.csv     # Dados para popular o banco
├── requirements.txt           # Dependências Python
├── RELEASE.md                 # Documentação de release
├── LICENSE                    # Licença Creative Commons BY 4.0
├── iniciar_sistema.bat        # Script para iniciar o sistema no Windows
└── README.md                  # Este arquivo
```

## ⚙️ Funcionalidades

### Autenticação e Autorização
- ✅ **Login Seguro** - Autenticação com senhas hashadas (bcrypt)
- ✅ **4 Roles de Usuário** - Admin, Editor, Visualizador e User
- ✅ **Rate Limiting** - Proteção contra ataques de força bruta
- ✅ **Validação de Senhas** - Política de segurança robusta

### Gestão de Linhas
- ✅ **Cadastro de Linhas** - Adicionar novos registros de ônibus
- ✅ **Consulta com Filtros** - Busca otimizada por número, área, operador e tipo
- ✅ **Edição (CRUD Completo)** - Operações seguras de Alterar e Excluir
- ✅ **📜 Histórico de Linhas** - Rastreio completo de Criação, Alteração e Exclusão
- ✅ **Ficha Cadastral** - Interface de visualização detalhada
- ✅ **Exportação CSV** - Download dos resultados da consulta

### Administração (Admin/Editor)
- ✅ **Gerenciamento de Usuários** - Criar, editar e excluir usuários (apenas admin)
- ✅ **Alteração de Senhas** - Admin pode redefinir senhas de qualquer usuário
- ✅ **Tabelas de Referência** - Gerenciamento de serviços, áreas, operadores, etc.

### UI/UX
- ✅ **Design Moderno** - Interface responsiva
- ✅ **Timeout Automático** - Logout após 30 minutos de inatividade

## 🛠️ Desenvolvimento

### Adicionar nova tabela de referência
1. Adicione a definição no `utils/init_db.py`
2. Crie o formulário em `views/mod_cadastro_ref.py`

### Modificar Consultas
- Edite as funções em `models/db.py`. O projeto utiliza `sqlite3` e `pandas`.

### Adicionar novo usuário via código
```python
import uuid
import bcrypt

# Gere o hash da senha
pwd_hash = bcrypt.hashpw(b'SuaSenha@123', bcrypt.gensalt()).decode()

# Insira no banco via UI de admin ou direto no SQLite
```

## 📝 Notas Importantes

- 🔒 O banco de dados `database_RIO.db` é local. Faça backups periódicos se houver dados críticos.
- 🧹 Para limpar o banco e recomeçar do zero, apague o arquivo `.db` e rode `python utils/init_db.py`.
- 📋 As linhas excluídas não são deletadas permanentemente, são movidas para a tabela `LinhaExcluida` com registro de data, usuário e ofício de exclusão.
- 🏷️ Este projeto está sob licença **Creative Commons Attribution 4.0 (CC BY 4.0)**

## 🐛 Troubleshooting

**Módulo não encontrado:**
```bash
pip install -r requirements.txt
```

**Erro ao atualizar o banco (Locked):**
Certifique-se de que o App Streamlit ou outro visualizador de SQLite (DB Browser) não está mantendo a conexão aberta durante operações de escrita críticas.

**Usuário bloqueado:**
Aguarde 15 minutos ou peça ao admin para verificar o status no banco de dados.