from db import carregar_servicos, carregar_operadores, carregar_areas_operacionais

print("🔍 Testando carregamento de referências...")

try:
    # Testar cada função de carregamento
    print("\n📋 Testando carregar_servicos()...")
    df_servicos = carregar_servicos()
    print(f"  📊 Servicos: {len(df_servicos)} registros")
    if not df_servicos.empty:
        print(f"  📝 Exemplo: {df_servicos.iloc[0].to_dict() if len(df_servicos) > 0 else 'Nenhum'}")

    print("\n📋 Testando carregar_operadores()...")
    df_operadores = carregar_operadores()
    print(f"  📊 Operadores: {len(df_operadores)} registros")
    if not df_operadores.empty:
        print(f"  📝 Exemplo: {df_operadores.iloc[0].to_dict() if len(df_operadores) > 0 else 'Nenhum'}")

    print("\n📋 Testando carregar_areas_operacionais()...")
    df_areas = carregar_areas_operacionais()
    print(f"  📊 Áreas Operacionais: {len(df_areas)} registros")
    if not df_areas.empty:
        print(f"  📝 Exemplo: {df_areas.iloc[0].to_dict() if len(df_areas) > 0 else 'Nenhum'}")

    print("\n✅ Teste concluído!")

except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()