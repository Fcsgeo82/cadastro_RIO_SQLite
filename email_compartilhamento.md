# Sugestão de E-mail para a Equipe de Dados

Copie o conteúdo abaixo para enviar à equipe de dados:

***

**Assunto:** Compartilhamento de Repositório - Novo Sistema de Cadastro e Consulta de Linhas (RIO Cadastro) para Homologação e Deploy

Prezada equipe de dados,

Espero que estejam bem.

Gostaria de compartilhar com vocês o repositório do novo **Sistema de Cadastro e Consulta de Linhas (RIO Cadastro)**. O projeto foi desenvolvido em **Streamlit (Python)** seguindo a arquitetura **MVC** e, nesta etapa, precisamos da colaboração de vocês para revisar a estrutura de banco de dados/autenticação e preparar a aplicação para deploy em nossa infraestrutura interna.

### 📋 Visão Geral do Sistema
O sistema foi concebido para gerenciar o cadastro e ciclo de vida das linhas de ônibus do Rio de Janeiro, contando com:
* **Interface Visual**: Desenvolvida em Streamlit com componentes dinâmicos de visualização de rotas e mapas.
* **Segurança e Níveis de Acesso**: Autenticação com 4 perfis distintos (*admin, editor, visualizador* e *user*), controle de força bruta (*rate limiting*) e expiração de sessão.
* **Rastreabilidade**: Histórico completo de auditoria (*criação, edição* e *exclusão* com justificativa de ofício) registrado na tabela `LogEventos`.
* **Módulo GTFS**: Interface administrativa para upload e substituição de pacotes geográficos GTFS (`.zip`).
* **Estrutura MVC**: Código segregado em `models/` (conexão e consultas SQLite), `views/` (páginas/telas da UI) e `utils/` (scripts de dados e UI).

---

### 🛠️ Próximas Etapas e Ajustes Necessários

Para viabilizar o deploy na infraestrutura da Secretaria, precisamos alinhar os seguintes pontos:

1. **Migração do Banco de Dados**: 
   Atualmente, o projeto utiliza um banco local **SQLite** (`database_RIO.db`). Precisamos migrar e apontar essas tabelas para o nosso banco de dados homologado/produção. Como as queries e conexões estão isoladas em `models/db.py` e `models/config.py`, essa adaptação deve ser direta.
2. **Integração de Autenticação / Login**:
   Hoje o login é feito com validação local da tabela `Usuarios` (com criptografia `bcrypt`). Precisamos definir se manteremos esse formato em produção ou se integraremos com algum provedor de Single Sign-On (SSO) da Secretaria.
3. **Pipeline de Deploy**:
   Disponibilizar a aplicação na nossa infraestrutura definitiva (ex: Docker, Kubernetes, VMs ou servidores internos).

---

### 🚀 Como testar localmente

Caso queiram testar a aplicação de imediato:
1. Clone o repositório.
2. Crie o ambiente virtual e instale as dependências (`pip install -r requirements.txt`).
3. Inicialize o banco SQLite localmente executando `python utils/init_db.py`.
4. Executar o Streamlit: `streamlit run app.py` (ou `python -m streamlit run app.py`).
5. **Dica (Windows)**: O projeto conta com o script `iniciar_sistema.bat` que automatiza o processo de ativação do ambiente e abre um túnel seguro temporário do **Pinggy** para gerar um link público `https://` compartilhável para testes rápidos.

A documentação detalhada do projeto, com as credenciais padrão de teste e a árvore MVC de arquivos, está disponível nos arquivos `README.md`, `RELEASE.md` e `CHANGELOG.md` na raiz do repositório.

Fico à disposição para agendarmos uma breve reunião para alinharmos os acessos e tirar dúvidas técnicas.

Atenciosamente,

**[Seu Nome/Assinatura]**  
[Seu Cargo]  
Secretaria Municipal de Transportes - SMTR
