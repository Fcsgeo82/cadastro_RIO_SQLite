import sqlite3
import uuid

def migrate():
    conn = sqlite3.connect('database_RIO.db')
    cursor = conn.cursor()
    
    print("Adding columns to Linha...")
    try:
        cursor.execute('ALTER TABLE Linha ADD COLUMN parametro_novo TEXT')
    except sqlite3.OperationalError:
        print("Column parametro_novo already exists")
    
    try:
        cursor.execute('ALTER TABLE Linha ADD COLUMN caracteristica TEXT')
    except sqlite3.OperationalError:
        print("Column caracteristica already exists")
    
    print("Creating Parametro and Caracteristica tables...")
    cursor.execute('CREATE TABLE IF NOT EXISTS Parametro (parametroID TEXT PRIMARY KEY, descricao TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Caracteristica (caracteristicaID TEXT PRIMARY KEY, descricao TEXT)')
    
    print("Populating tables...")
    cursor.execute('DELETE FROM Parametro')
    cursor.execute('INSERT INTO Parametro (parametroID, descricao) VALUES (?, ?), (?, ?), (?, ?)', 
                   (str(uuid.uuid4()), 'Polarizada', str(uuid.uuid4()), 'Inter-Região', str(uuid.uuid4()), 'Intra-Região'))
    
    cursor.execute('DELETE FROM Caracteristica')
    cursor.execute('INSERT INTO Caracteristica (caracteristicaID, descricao) VALUES (?, ?), (?, ?)', 
                   (str(uuid.uuid4()), 'Alimentadora', str(uuid.uuid4()), 'Inter-Bairro'))
    
    conn.commit()
    conn.close()
    print("Migration successful")

if __name__ == "__main__":
    migrate()
