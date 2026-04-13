# Sistema de Cadastro e Consulta de Linhas de Ônibus - RIO

## 📋 Release Notes v1.0

---

## 1. O que é este Sistema?

Este é um sistema de **cadastro e consulta de linhas de ônibus** desenvolvido para a cidade do Rio de Janeiro. O aplicativo permite gerenciar informações completas sobre as linhas de ônibus, incluindo:

- Dados cadastrais das linhas (número, serviço, operador, área operacional)
- Características técnicas (tipo de sistema, parâmetro, característica, grupamento BRS)
- Informações de frota (tipo de veículo, ofícios relacionados)
- Itinerários (pontos de parada, logradouros, bairros)
- Histórico de alterações

### Principais Funcionalidades

✅ **Consulta de Linhas** - Busca filtrada por número, área operacional, operador, tipo de operação, etc.

✅ **Cadastro de Novas Linhas** - Interface completa para registro de novas linhas (função administrativa)

✅ **Edição de Linhas** - Alteração de dados existentes (função administrativa)

✅ **Histórico de Alterações** - Registro de todas as modificações feitas em cada linha

✅ **Exclusão com Registro** - Linhas excluídas são movidas para uma tabela histórica para consulta futura

✅ **Fichas Detalhadas** - Visualização completa de cada linha com todos os dados

✅ **Tabelas de Referência** - Gerenciamento de dados auxiliares (operadores, áreas, tipos de sistema, etc.)

✅ **Gestão de Usuários** - Controle de acesso e permissões (função administrativa)

---

## 2. Tecnologias Utilizadas

- **Frontend**: Streamlit (Python)
- **Backend**: SQLite (banco de dados local)
- **Linguagem**: Python
- **Hospedagem**: Pode ser executado localmente ou em servidores como Streamlit Cloud

---

## 3. Estrutura do Banco de Dados

### Tabelas Principais

| Tabela | Descrição |
|--------|-----------|
| **Linha** | Dados principais das linhas de ônibus |
| **LinhaExcluida** | Histórico de linhas excluídas (não deletes definitivos) |
| **Operador** | Empresas de ônibus |
| **AreaOperacional** | Áreas operacionais da cidade |
| **Servico** | Tipos de serviço (ex: comum, executivo) |
| **TipoSistema** | Tipo de operação (ex: convencional, articulado) |
| **Parametro** | Parâmetros de operação |
| **Caracteristica** | Características da linha |
| **TipoVeiculo** | Tipos de veículo autorizados |
| **GrupamentoBRS** | Grupamentos de faixa prioritas BRS |
| **Oficio** | Ofícios da SMTR relacionados |
| **Itinerario** | Pontos de parada de cada linha |
| **Usuarios** | Usuários do sistema com níveis de acesso |

---

## 4. Níveis de Acesso

O sistema possui três níveis de acesso:

### 👤 Usuário (user)
- Consultar linhas ativas
- Visualizar fichas
- Ver histórico

### ✏️ Editor
- Tudo do usuário +
- Cadastrar novas linhas
- Editar linhas existentes
- Tabelas de referência
- **Consultar linhas excluídas e suas fichas**

### 👑 Administrador (admin)
- Tudo do editor +
- Gerenciar usuários
- Excluir linhas
- **Consultar linhas excluídas e suas fichas**

---

## 5. Como Instalar e Executar

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passos de Instalação

1. **Clone o repositório**

2. **Crie um ambiente virtual (recomendado):**
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual:**
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Inicialize o banco de dados:**
   ```bash
   python init_db.py
   ```

6. **Execute o aplicativo:**
   ```bash
   streamlit run app.py
   ```

7. **Acesse no navegador:**
   - URL padrão: `http://localhost:8501`

---

## 6. Credenciais Padrão

Após a primeira execução, o sistema cria automaticamente dois usuários:

| Usuário | Senha | Função |
|---------|-------|--------|
| admin | admin123 | Administrador |
| editor | editor123 | Editor |
| user | user123 | Usuário |


⚠️ **Recomendação**: Altere as senhas padrão após o primeiro acesso!

---

## 7. Como Usar o Sistema

### 7.1 Login

Ao abrir o sistema, você verá a tela de login. Insira seu usuário e senha para acessar.

### 7.2 Consulta de Linhas

1. Na aba "Consultar Linhas", utilize os filtros disponíveis:
   - Busca geral (pesquisa em qualquer campo)
   - Número da linha
   - Área operacional
   - Operador
   - Tipo de operação
   - Parâmetro
   - Característica
   - Frota autorizada
   - Grupamento BRS

2. Clique em "Buscar" ou "Listar Todas"

3. Selecione uma linha na tabela para ver as ações disponíveis:
   - 👁️ Ver Ficha
   - ✏️ Alterar (apenas admin/editor)
   - 🕰️ Histórico
   - 🗑️ Excluir (apenas admin)

### 7.3 Cadastro de Linha (Editor/Admin)

1. Acesse a aba "Cadastrar Linha"
2. Preencha os campos obrigatórios (marcados com *)
3. Adicione os itinerários (ida e volta)
4. Clique em "Salvar"

### 7.4 Exclusão de Linha (Admin)

1. Selecione a linha na aba de consulta
2. Clique em "Excluir"
3. **Selecione um Ofício de Exclusão** (obrigatório)
4. Confirme a exclusão

⚠️ A linha não é deletada definitivamente! Ela é movida para a tabela de linhas excluídas com registro da data, usuário e ofício.

### 7.5 Linhas Excluídas (Editor/Admin)

1. Acesse a aba "Linhas Excluídas"
2. Visualize todas as linhas excluídas
3. Selecione uma linha para ver sua ficha completa
4. Os dados incluem:
   - Todos os dados da linha no momento da exclusão
   - Ofício de exclusão
   - Data e hora da exclusão
   - Usuário que realizou a exclusão

---

## 8. Estrutura de Arquivos

```
cadastro_RIO_SQLite/
├── app.py                 # Arquivo principal do Streamlit
├── db.py                  # Funções de banco de dados
├── config.py              # Configurações de conexão
├── init_db.py             # Script de inicialização do banco
├── mod_consulta.py        # Módulo de consulta
├── mod_cadastro.py        # Módulo de cadastro
├── mod_edicao.py         # Módulo de edição
├── mod_ficha.py          # Módulo de visualização de ficha
├── mod_historico.py      # Módulo de histórico
├── mod_usuarios.py       # Módulo de gestão de usuários
├── mod_cadastro_ref.py   # Módulo de tabelas de referência
├── database_RIO.db       # Banco de dados SQLite (criado automaticamente)
├── logo_rio.png          # Logo do sistema (opcional)
├── logo_rio.svg         # Logo do sistema (opcional)
└── requirements.txt     # Dependências do Python
```

---

## 9. Personalização

### Adicionar Logo

Coloque um arquivo `logo_rio.png` ou `logo_rio.svg` na pasta do projeto para exibir no header.

### Configurar Email para Reset de Senha

Edite o arquivo `.streamlit/secrets.toml`:
```toml
GMAIL_USER = "seu-email@gmail.com"
GMAIL_APP_PASS = "sua-senha-de-app"
APP_URL = "https://sua-url.streamlit.app"
```

---

## 10. Suporte e Contribuição

Para dúvidas, sugestões ou relatórios de bugs, entre em contato através do repositório GitHub.

---

## 11. Licença

Este projeto está disponível sob licença Creative Commons Atribuição 4.0 Internacional (CC BY 4.0).

---

**Desenvolvido para a gestão de linhas de ônibus do Rio de Janeiro**