import csv
import json

# === 1. Cargar el nomenclator JSON ===
with open("getNomenclator.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Aplanamos todos los "amb[x].ambitos" en una sola lista
todos_los_ambitos = []
for bloque in data.get("amb", []):
    todos_los_ambitos.extend(bloque.get("ambitos", []))

# Crear un índice rápido: co → objeto
indice_por_co = {item.get("co"): item for item in todos_los_ambitos if item.get("co")}

# === 2. Leer CSV original con los CO ===
resultado = []

with open("mesas_con_ids_y_cos.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)  # saltar encabezado si lo tiene

    for fila in reader:
        co = fila[1].strip()  # columna B

        entrada = indice_por_co.get(co)

        if entrada:
            r = entrada.get("r", [])

            if len(r) == 4:
                # Aseguramos que sean enteros
                r_int = [int(x) for x in r]

                # Ordenamos y tomamos los valores intermedios
                ordenados = sorted(r_int)
                intermedio1, intermedio2 = ordenados[1], ordenados[2]

                id2, id3 = intermedio1, intermedio2
            else:
                id2 = id3 = None
        else:
            id2 = id3 = None

        resultado.append([co, id2, id3])

# === 3. Guardar el resultado ===
with open("cos_con_ids_extraidos.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["co", "id2_intermedio", "id3_intermedio"])
    writer.writerows(resultado)

print("Listo. Archivo generado: cos_con_ids_extraidos.csv")
