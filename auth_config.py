import bcrypt

# Usuários e senhas (senhas hashadas com bcrypt)
# Para adicionar usuários: gere hash com bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
# Ou use o script gerar_hash.py
USUARIOS = {
    "admin": {
        "senha": "$2b$12$8w3lHPYK41V2SIZL6ECIMet/DNVpf0/nWx28cwGAXq1CkdgLGvRw.",  # admin123
        "nome": "Administrador",
        "email": "admin@exemplo.com"
    },
    "usuario1": {
        "senha": "$2b$12$5FXEWj2hNSesjuVHnbh9jOpo2OORO9062KGSQzRUSQefSl1ZpYJuy",  # usuario123
        "nome": "Usuário 1",
        "email": "usuario1@exemplo.com"
    }
}

def verificar_senha(senha_digitada: str, senha_hashada: str) -> bool:
    """Verifica se a senha digitada corresponde ao hash."""
    return bcrypt.checkpw(senha_digitada.encode(), senha_hashada.encode())

def adicionar_usuario(username: str, senha: str, nome: str, email: str):
    """Adiciona novo usuário (usar apenas para setup inicial)."""
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
    USUARIOS[username] = {
        "senha": senha_hash.decode(),  # Converte bytes para string
        "nome": nome,
        "email": email
    }