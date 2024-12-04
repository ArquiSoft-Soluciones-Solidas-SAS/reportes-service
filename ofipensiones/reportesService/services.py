import mongoengine
from django.db.models import Q
from datetime import date, timedelta

from pymongo import MongoClient

from .models import Curso, DetalleCobroCurso, ReciboCobro, ReciboPago, Institucion, Estudiante, CronogramaBase

from django.db import connection

from mongoengine.queryset.visitor import Q


from pymongo import MongoClient

def obtener_cuentas_por_cobrar(nombre_institucion, mes):
    print("Hit the DB")

    # Conexión a la base de datos de MongoDB
    db = mongoengine.get_db()
    # Conexión a la colección de MongoDB
    collection = db["recibos_cobro"]
    print(collection)

def obtener_cartera_general(nombre_institucion, mes):
    print("Hit the DB")

    # Filtrar cronogramas base por la institución y obtener los detalles del mes
    cronogramas = CronogramaBase.objects.filter(
        nombreInstitucion=nombre_institucion
    ).only("id", "detalle_cobro")

    total_deuda = 0.0

    for cronograma in cronogramas:
        # Filtrar detalles del cronograma para el mes específico
        detalles_mes = [detalle for detalle in cronograma.detalle_cobro if detalle.mes == mes]
        for detalle_cobro in detalles_mes:
            # Buscar recibos no pagados relacionados con este detalle
            recibos = ReciboCobro.objects.filter(
                detalles_cobro__id=detalle_cobro.id,
                estudiante__nombreInstitucion=nombre_institucion,
                id__nin=ReciboPago.objects.distinct("recibo_cobro")  # Recibos no pagados
            ).only("nmonto")

            # Sumar los montos de los recibos
            total_deuda += sum(float(recibo.nmonto) for recibo in recibos)

    return [{
        "institucion": nombre_institucion,
        "mes": mes,
        "total_deuda": total_deuda
    }]




