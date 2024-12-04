from django.db.models import Q
from datetime import date, timedelta

from pymongo import MongoClient

from .models import Curso, DetalleCobroCurso, ReciboCobro, ReciboPago, Institucion, Estudiante, CronogramaBase

from django.db import connection

from mongoengine.queryset.visitor import Q


from pymongo import MongoClient

def obtener_cuentas_por_cobrar(nombre_institucion, mes):
    print("Hit the DB")

    client = MongoClient('mongodb://microservicios_user:password@10.128.0.87:27017')
    db = client['reportes-query-service']

    resultados = db["recibo_cobro"].aggregate([
        # Lookup para recibos pagos
        {
            "$lookup": {
                "from": "recibo_pago",
                "localField": "_id",
                "foreignField": "recibo_cobro",
                "as": "pagos"
            }
        },
        # Filtrar recibos no pagados
        {
            "$match": {
                "pagos": {"$eq": []}
            }
        },
        # Lookup para obtener detalles del estudiante
        {
            "$lookup": {
                "from": "estudiante",
                "localField": "estudiante",
                "foreignField": "_id",
                "as": "estudiante_info"
            }
        },
        {"$unwind": "$estudiante_info"},
        # Filtrar por nombre de la institución
        {
            "$match": {
                "estudiante_info.nombreInstitucion": nombre_institucion
            }
        },
        # Lookup para obtener detalles del cronograma base
        {
            "$lookup": {
                "from": "cronograma_base",
                "localField": "detalles_cobro.cronograma_curso_id",  # Asegúrate de que este campo sea correcto
                "foreignField": "_id",
                "as": "cronograma_info"
            }
        },
        {"$unwind": "$cronograma_info"},
        # Filtrar por el mes en detalles de cobro
        {
            "$match": {
                "detalles_cobro.mes": mes
            }
        },
        # Proyecto final para devolver la estructura requerida
        {
            "$project": {
                "monto_recibo": {"$toDouble": "$nmonto"},
                "mes": "$detalles_cobro.mes",
                "valor_detalle": {"$toDouble": "$detalles_cobro.valor"},
                "estudiante_id": {"$toString": "$estudiante_info._id"},
                "nombre_estudiante": "$estudiante_info.nombreEstudiante",
                "nombre_grado": "$cronograma_info.grado",
                "nombre_institucion": nombre_institucion,
                "nombre_concepto": "$cronograma_info.nombre",
                "codigo": "$cronograma_info.codigo"
            }
        }
    ])

    # Convertir los resultados a una lista de diccionarios
    return list(resultados)




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




