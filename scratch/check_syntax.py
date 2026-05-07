import py_compile
import os
import sys

files_to_check = [
    "app.py",
    "utils/ui_components.py",
    "views/mod_consulta.py",
    "views/mod_ficha.py",
    "views/mod_edicao.py",
    "views/mod_cadastro.py",
    "views/mod_cadastro_ref.py",
    "views/mod_historico.py",
    "views/mod_usuarios.py"
]

all_ok = True
for f in files_to_check:
    try:
        py_compile.compile(f, doraise=True)
        print(f"OK: {f}")
    except py_compile.PyCompileError as e:
        print(f"FAIL: {f} Syntax Error\n{e}")
        all_ok = False
    except Exception as e:
        print(f"ERROR: {f} {e}")
        all_ok = False

if not all_ok:
    sys.exit(1)
