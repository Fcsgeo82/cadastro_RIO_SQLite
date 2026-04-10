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

3. **Inicializar o Banco de Dados:**
   Este passo cria as tabelas e popula com dados iniciais (Serviços, Operadores, Áreas, etc).
   ```bash
   python init_db.py
   ```

### Executar a Aplicação

```bash
streamlit run app.py
ou
python -m streamlit run app.py #Caso o streamlit não esteja no path.
```

Acesse em: http://localhost:8501

## 🔐 Login e Autenticação

O sistema possui 3 tipos de usuários com permissões diferentes:

| Usuário | Senha | Permissões |
|---------|-------|------------|
| **admin** | Admin@123 | Todas as abas (Consulta, Cadastro, Tabelas de Referência, Usuários) |
| **editor** | Editor@123 | Consulta, Cadastro, Tabelas de Referência |
| **user** | User@123 | Apenas Consulta |

> ⚠️ As senhas iniciais acima devem ser alteradas após a inicialização do banco de dados, quando o usuário executar o arquivo app.py pela primeira vez. Trata-se de uma medida de segurança imediata e imprescindível para a proteção do sistema.

> ⚠️ **Nota**: A senha inicial deve ser alterada conforme a política de segurança (mínimo 8 caracteres, 1 maiúscula, 1 número, 1 símbolo).

### Políticas de Segurança

- **Rate Limiting**: Após 5 tentativas incorretas, a conta é bloqueada por 15 minutos
- **Validação de Senha**: Mínimo 8 caracteres, 1 letra maiúscula, 1 número, 1 símbolo especial

## 📁 Estrutura de Pastas

```
cadastro_RIO_SQLite/
├── app.py                 # Aplicação principal Streamlit
├── config.py              # Conexão com SQLite
├── db.py                  # Operações de Banco de Dados (CRUD + Auth)
├── init_db.py             # Script de inicialização do banco de dados
├── database_RIO.db        # Banco de dados SQLite (gerado após init_db)
├── mod_cadastro.py        # Módulo UI: Cadastro de linhas
├── mod_consulta.py        # Módulo UI: Consulta de linhas
├── mod_cadastro_ref.py    # Módulo UI: Cadastro de tabelas de ref
├── mod_edicao.py          # Módulo UI: Edição completa de registros
├── mod_ficha.py           # Módulo UI: Ficha cadastral detalhada
├── mod_historico.py       # Módulo UI: Histórico e rastreamento de revisões
├── mod_usuarios.py        # Módulo UI: Gerenciamento de usuários (apenas admin)
├── Schema.csv             # Definição do esquema das tabelas
├── requirements.txt       # Dependências Python
└── README.md              # Este arquivo
```

## ⚙️ Funcionalidades

### Autenticação e Autorização
- ✅ **Login Seguro** - Autenticação com senhas hashadas (bcrypt)
- ✅ **3 Roles de Usuário** - Admin, Editor, User com permissões específicas
- ✅ **Rate Limiting** - Proteção contra ataques de força bruta
- ✅ **Validação de Senhas** - Política de segurança robusta

### Gestão de Linhas
- ✅ **Cadastro de Linhas** - Adicionar novos registros de ônibus
- ✅ **Consulta com Filtros** - Busca otimizada por número, área, operador e tipo
- ✅ **Edição (CRUD Completo)** - Operações seguras de Alterar e Excluir
- ✅ **Ficha Cadastral** - Interface de visualização detalhada
- ✅ **Histórico e Revisões** - Rastreio automático de atualizações
- ✅ **Exportação CSV** - Download dos resultados da consulta

### Administração (apenas Admin)
- ✅ **Gerenciamento de Usuários** - Criar, editar e excluir usuários
- ✅ **Alteração de Senhas** - Admin pode redefinir senhas de qualquer usuário

### UI/UX
- ✅ **Design Moderno** - Interface responsiva com tipografia limpa
- ✅ **Tabelas de Referência** - Gerenciamento dinâmico de serviços, áreas e operadores
- ✅ **Timeout Automático** - Logout após 30 minutos de inatividade

## 🛠️ Desenvolvimento

### Adicionar nova tabela
1. Adicione a definição no `Schema.csv`
2. Atualize o `init_db.py` com dados iniciais se necessário
3. Crie o formulário em `mod_cadastro_ref.py`

### Modificar Consultas
- Edite as funções no `db.py`. O projeto utiliza a biblioteca padrão `sqlite3` e `pandas` para retornar DataFrames.

### Adicionar novo usuário via código
```python
import uuid
import bcrypt

# Gere o hash da senha
pwd_hash = bcrypt.hashpw(b'SuaSenha@123', bcrypt.gensalt()).decode()

# Insira no banco (via SQLite ou admin UI)
```

## 📝 Notas Importantes

- 🔒 O banco de dados `database_RIO.db` é local. Faça backups periódicos se houver dados críticos.
- 🧹 Para limpar o banco e recomeçar do zero, apague o arquivo `.db` e rode `python init_db.py`.
- ⚙️ O arquivo `auth_config.py` foi substituído pelo sistema de autenticação baseado em banco de dados.

## 🐛 Troubleshooting

**Módulo não encontrado:**
```bash
pip install -r requirements.txt
```

**Erro ao atualizar o banco (Locked):**
Certifique-se de que o App Streamlit ou outro visualizador de SQLite (DB Browser) não está mantendo a conexão aberta durante operações de escrita críticas.

**Usuário bloqueado:**
Aguarde 15 minutos ou peça ao admin para verificar o status no banco de dados.