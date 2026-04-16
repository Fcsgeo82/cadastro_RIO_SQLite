import sqlite3

oficios = {
    "Of\xedcio SMTR-RIO 02/2026": "b44d69e7-c9d1-4c92-ad12-418691dba37a",
    "Of\xedcio SMTR-RIO 01/2026": "81e4119b-f67c-4b13-a95e-409062204c49",
    "Of\xedcio SMTR-RIO 03/2026": "2690d1fc-d2b5-4407-b5c8-602a37ad7bcf"
}

of_id = "2690d1fc-d2b5-4407-b5c8-602a37ad7bcf"

def _obter_label(dic, chave):
    if not chave:
        return "-"
    for label, id_ in dic.items():
        if str(id_) == str(chave):
            return label
    return chave

result = _obter_label(oficios, of_id)
print(f"Result: {result}")