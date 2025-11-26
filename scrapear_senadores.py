#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import csv
import requests
import time

STRUCTURE_FILE = "response_structure.json"
CSV_FILE = "cos_con_ids_extraidos.csv"
OUTPUT_FILE = "resultados_senador_mesas.json"

COOKIE_ACTUALIZADA = ("_ga_FD1T68DDF3=GS1.1.1744320354.1.1.1744320803.20.0.0; "
                      "_ga_1LC2CWY6VE=GS2.1.s1754851657$o1$g1$t1754851852$j60$l0$h0; "
                      "_ga_YCMT9Y4XSM=GS2.1.s1757977788$o2$g1$t1757978006$j60$l0$h447930829; "
                      "_ga_L81N17LJGK=GS2.3.s1760027225$o1$g0$t1760027225$j60$l0$h0; "
                      "_ga=GA1.1.2147232300.1744320354; "
                      "_ga_1Y379TMGM5=GS2.1.s1762873509$o22$g0$t1762873604$j60$l0$h0")

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "es-419,es;q=0.9,en;q=0.8,it;q=0.7,gl;q=0.6",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Origin": "https://resultados.eleccionesbonaerenses.gba.gob.ar",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors", 
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=1, i",
    "Cookie": COOKIE_ACTUALIZADA
}

def cargar_csv_con_ids():
    """Cargar el CSV con los IDs de senador"""
    mesas = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            co = row['co']
            id_senador = row['id2_intermedio']
            # Solo agregar si tiene ID de senador válido
            if id_senador and id_senador.strip() and id_senador != '-1':
                mesas.append({
                    'co': co,
                    'id_senador': int(id_senador)
                })
    return mesas

def crear_mapeo_co_a_hash(structure):
    """Crear un diccionario de co -> hash 'c' desde el structure"""
    mapeo = {}
    
    def rec(node):
        if isinstance(node, dict):
            if node.get("l") == 70:
                co = node.get("co")
                c = node.get("c")
                if co and c:
                    mapeo[co] = c
            for v in node.values():
                rec(v)
        elif isinstance(node, list):
            for it in node:
                rec(it)
    
    rec(structure)
    return mapeo

def fetch_mesa_senador(hash_c, id_senador):
    """Obtener resultados de SENADOR PROVINCIAL con el ID correcto"""
    # Scope 5 = Senador Provincial
    url = f"https://resultados.eleccionesbonaerenses.gba.gob.ar/backend-difu/scope/data/getScopeDataMap/{hash_c}/5/0/-1"
    
    headers = BASE_HEADERS.copy()
    # Referer con el ID correcto de senador (identificador 0)
    headers["Referer"] = f"https://resultados.eleccionesbonaerenses.gba.gob.ar/resultados/0/{id_senador}/-1"
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        return r.status_code, r
    except Exception as e:
        return None, e

def probar_varias_mesas(mesas_con_hash, cantidad=10):
    """Probar varias mesas para ver cuáles funcionan"""
    print(f"\n=== PROBANDO {cantidad} MESAS ALEATORIAS ===\n")
    
    import random
    mesas_muestra = random.sample(mesas_con_hash, min(cantidad, len(mesas_con_hash)))
    
    mesas_funcionan = []
    
    for mesa in mesas_muestra:
        co = mesa['co']
        id_sen = mesa['id_senador']
        hash_c = mesa['hash']
        
        print(f"Mesa {co} (ID:{id_sen})... ", end="", flush=True)
        
        status, resp = fetch_mesa_senador(hash_c, id_sen)
        
        if status == 200 and resp and len(resp.text) > 0:
            try:
                data = resp.json()
                if "partidos" in data and len(data["partidos"]) > 0:
                    print(f"✅ ({len(data['partidos'])} partidos)")
                    mesas_funcionan.append(mesa)
                else:
                    print("⚠️  Sin partidos")
            except:
                print("❌ JSON inválido")
        elif status == 403:
            print("❌ 403")
        else:
            print(f"❌ Status {status}")
    
    return mesas_funcionan

if __name__ == "__main__":
    print("="*60)
    print("🗳️  SCRAPER SENADOR PROVINCIAL - CON IDs DEL CSV")
    print("="*60)
    
    # 1. Cargar CSV con IDs de senador
    print(f"\n📄 Cargando {CSV_FILE}...")
    mesas_csv = cargar_csv_con_ids()
    print(f"✅ Mesas con ID de senador en CSV: {len(mesas_csv):,}")
    
    if len(mesas_csv) == 0:
        print("❌ No se encontraron mesas con ID de senador en el CSV")
        exit(1)
    
    # 2. Cargar structure para obtener los hash
    print(f"\n📄 Cargando {STRUCTURE_FILE}...")
    with open(STRUCTURE_FILE, "r", encoding="utf-8") as f:
        structure = json.load(f)
    
    # 3. Crear mapeo de co -> hash
    print("🔗 Creando mapeo co -> hash...")
    co_a_hash = crear_mapeo_co_a_hash(structure)
    print(f"✅ Mapeo creado con {len(co_a_hash):,} mesas")
    
    # 4. Combinar datos: agregar hash a cada mesa del CSV
    mesas_completas = []
    mesas_sin_hash = []
    
    for mesa in mesas_csv:
        co = mesa['co']
        if co in co_a_hash:
            mesas_completas.append({
                'co': co,
                'id_senador': mesa['id_senador'],
                'hash': co_a_hash[co]
            })
        else:
            mesas_sin_hash.append(co)
    
    print(f"\n📊 Mesas completas (con hash): {len(mesas_completas):,}")
    if mesas_sin_hash:
        print(f"⚠️  Mesas sin hash encontrado: {len(mesas_sin_hash)}")
        print(f"   Primeras 5: {mesas_sin_hash[:5]}")
    
    if len(mesas_completas) == 0:
        print("❌ No hay mesas con datos completos")
        exit(1)
    
    # 5. Mostrar ejemplos y rangos
    print(f"\n📋 Primeras 3 mesas de ejemplo:")
    for mesa in mesas_completas[:3]:
        print(f"  - CO: {mesa['co']}, ID Senador: {mesa['id_senador']}, Hash: {mesa['hash'][:15]}...")
    
    ids_senador = [m['id_senador'] for m in mesas_completas]
    print(f"\n🔢 Rango de IDs de senador: {min(ids_senador):,} a {max(ids_senador):,}")
    
    # 6. Prueba con muestra
    mesas_prueba = 20
    mesas_funcionan = probar_varias_mesas(mesas_completas, mesas_prueba)
    
    if not mesas_funcionan:
        print("\n❌ Ninguna mesa funcionó. Revisar cookies o estructura.")
        exit(1)
    
    # 7. Estimación
    tasa_exito = len(mesas_funcionan) / mesas_prueba * 100
    mesas_estimadas = int(len(mesas_completas) * len(mesas_funcionan) / mesas_prueba)
    tiempo_estimado = len(mesas_completas) * 0.1 / 60
    
    print(f"\n{'='*60}")
    print(f"📈 ESTIMACIÓN:")
    print(f"{'='*60}")
    print(f"✅ Exitosas en prueba: {len(mesas_funcionan)}/{mesas_prueba} ({tasa_exito:.1f}%)")
    print(f"📊 Mesas estimadas con datos: ~{mesas_estimadas:,} de {len(mesas_completas):,}")
    print(f"⏱️  Tiempo estimado: ~{tiempo_estimado:.1f} minutos")
    print(f"{'='*60}\n")
    
    # 8. Preguntar si continuar
    respuesta = input(f"¿Descargar TODAS las {len(mesas_completas):,} mesas? (s/n): ")
    if respuesta.lower() != 's':
        print("❌ Abortado")
        exit(0)
    
    # 9. Descarga completa
    resultados = {}
    errores = []
    total = len(mesas_completas)
    
    print(f"\n🚀 Descargando {total:,} mesas...\n")
    
    tiempo_inicio = time.time()
    
    for idx, mesa in enumerate(mesas_completas, 1):
        co = mesa['co']
        id_sen = mesa['id_senador']
        hash_c = mesa['hash']
        
        print(f"[{idx}/{total}] {co} (ID:{id_sen})... ", end="", flush=True)
        
        status, resp = fetch_mesa_senador(hash_c, id_sen)
        
        if status == 200 and resp and len(resp.text) > 0:
            try:
                data = resp.json()
                if "partidos" in data and len(data["partidos"]) > 0:
                    resultados[co] = {
                        "id_senador": id_sen,
                        "hash": hash_c,
                        "data": data
                    }
                    print(f"✅ ({len(data['partidos'])} partidos)")
                else:
                    print("⏭️  Sin partidos")
            except Exception as e:
                print(f"❌ JSON")
                errores.append({"co": co, "id_senador": id_sen, "error": "json_error"})
        elif status == 403:
            print("❌ 403")
            errores.append({"co": co, "id_senador": id_sen, "error": "403_forbidden"})
        else:
            print(f"❌ {status}")
            errores.append({"co": co, "id_senador": id_sen, "error": f"status_{status}"})
        
        time.sleep(0.1)
        
        # Progreso cada 100 mesas
        if idx % 100 == 0:
            exitosas = len(resultados)
            tasa_real = exitosas / idx * 100
            tiempo_transcurrido = time.time() - tiempo_inicio
            tiempo_restante = (total - idx) * tiempo_transcurrido / idx / 60
            print(f"--- {idx}/{total} ({idx*100//total}%) - ✅: {exitosas} ({tasa_real:.1f}%) - ⏱️ {tiempo_restante:.1f}min ---")
    
    # 10. Guardar resultados
    print(f"\n💾 Guardando {len(resultados):,} resultados...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    # 11. Guardar errores si los hay
    if errores:
        error_file = "errores_senador.json"
        with open(error_file, "w", encoding="utf-8") as f:
            json.dump(errores, f, ensure_ascii=False, indent=2)
        print(f"⚠️  Errores guardados en: {error_file}")
    
    # 12. Resumen final
    tiempo_total = time.time() - tiempo_inicio
    print("\n" + "="*60)
    print("🎉 RESUMEN FINAL - SENADOR PROVINCIAL")
    print("="*60)
    print(f"📊 Mesas procesadas: {total:,}")
    print(f"✅ Resultados exitosos: {len(resultados):,}")
    print(f"❌ Errores: {len(errores):,}")
    print(f"📈 Tasa de éxito: {len(resultados)*100//total if total > 0 else 0}%")
    print(f"⏱️  Tiempo total: {tiempo_total/60:.1f} minutos")
    print(f"💾 Archivo de resultados: {OUTPUT_FILE}")
    
    if len(resultados) > 0:
        partidos_totales = sum(len(r["data"].get("partidos", [])) for r in resultados.values())
        partidos_promedio = partidos_totales // len(resultados)
        print(f"👥 Partidos por mesa (promedio): {partidos_promedio}")
    print("="*60)