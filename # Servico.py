    # Servico
    cursor.executemany("INSERT OR IGNORE INTO Servico (servicoID, Prefixo, descricao) VALUES (?, ?, ?)", [
        ("S1", "", "Regular"),
        ("S2", "ST", "Temporário"),
        ("S3", "SR", "Rápido"),
        ("S4", "SV", "Variante"),
        ("S5", "SN", "Noturno"),
        ("S6", "SP", "Parcial"),
        ("S7", "SE", "Experimental"),
    ])
    
    # Operador
    cursor.executemany("INSERT OR IGNORE INTO operador (operadorID, nomeFantasia, razaoSocial) VALUES (?, ?, ?)", [
        ("O1", "A2", "Comporte"),
        ("O2", "B2", "Comporte"),
    ])
    
    # AreaOperacional
    cursor.executemany("INSERT OR IGNORE INTO AreaOperacional (areaOperacionalID, descricao) VALUES (?, ?)", [
        ("A1", "Centro"),
        ("A2", "Zona Sul"),
        ("A3", "Zona Norte"),
        ("A4", "Zona Oeste"),
    ])
    
    # TipoSistema
    cursor.executemany("INSERT OR IGNORE INTO TipoSistema (tipoSistemaID, descricao) VALUES (?, ?)", [
        ("T1", "Convencional"),
        ("T2", "Executivo"),
        ("T3", "Alimentador"),
    ])
    
    # TipoVeiculo
    cursor.executemany("INSERT OR IGNORE INTO TipoVeiculo (tipoVeiculoID, descricao) VALUES (?, ?)", [
        ("V1", "Ônibus Urbano"),
        ("V2", "Micro-ônibus"),
        ("V3", "Articulado"),
    ])

    # GrupamentoBRS
    cursor.executemany("INSERT OR IGNORE INTO GrupamentoBRS (grupamentoBRSID, descricao) VALUES (?, ?)", [
        ("1", 1),
        ("2", 2),
        ("3", 3),
    ])