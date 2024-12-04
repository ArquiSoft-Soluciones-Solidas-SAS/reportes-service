from django.http import JsonResponse
from django.shortcuts import render
from .services import obtener_cuentas_por_cobrar, obtener_cartera_general
#import redis
import json


def generar_reporte(request, nombre_institucion, mes):
    key = f"cuentas_por_cobrar:{nombre_institucion}:{mes}"
    print(f"Key: {key}")

    # r = redis.StrictRedis(host='10.128.0.5', port=6379, db=0)
    # cuentas_por_cobrar = r.get(key)
    cuentas_por_cobrar = None

    if cuentas_por_cobrar is not None:
        cuentas_por_cobrar = json.loads(cuentas_por_cobrar.decode('utf-8'))
        print("Hit Redis")
    else:
        print("No se encontraron datos en Redis, ejecutando la función...")
        nombre_institucion_con_espacios = nombre_institucion.replace('_', ' ')
        mes_con_espacios = mes.replace('_', ' ')

        try:
            print("Obteniendo cuentas por cobrar: ", nombre_institucion_con_espacios, mes_con_espacios)
            cuentas_por_cobrar = obtener_cuentas_por_cobrar(nombre_institucion_con_espacios, mes_con_espacios)
            print("Datos obtenidos de la función:", cuentas_por_cobrar)
            # r.set(key, json.dumps(cuentas_por_cobrar), ex=60 * 60 * 24)
        except Exception as e:
            print(f"Error al obtener cuentas por cobrar: {e}")
            cuentas_por_cobrar = []

    #return render(request, 'listar.html', {'cuentas_por_cobrar': cuentas_por_cobrar})
    return cuentas_por_cobrar
