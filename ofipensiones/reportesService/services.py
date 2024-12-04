from django.db.models import Q
from datetime import date, timedelta

from pymongo import MongoClient

from .models import Curso, DetalleCobroCurso, ReciboCobro, ReciboPago, Institucion, Estudiante, CronogramaBase

from django.db import connection

from mongoengine.queryset.visitor import Q


from pymongo import MongoClient

from pymongo import MongoClient

def obtener_cuentas_por_cobrar(nombre_institucion, mes):
    print("Ejecutando consulta...")

    # Conexión a la base de datos
    client = MongoClient('mongodb://microservicios_user:password@10.128.0.87:27017')
    db = client['reportes-query-service']

    # Pipeline
    pipeline = [
        {
            "$lookup": {
                "from": "recibo_pago",
                "localField": "_id",
                "foreignField": "recibo_cobro",
                "as": "pagos"
            }
        },
        {
            "$match": {
                "pagos": {"$size": 0}
            }
        },
        {
            "$lookup": {
                "from": "estudiante",
                "localField": "estudiante",
                "foreignField": "_id",
                "as": "estudiante"
            }
        },
        {"$unwind": "$estudiante"},
        {
            "$lookup": {
                "from": "institucion",
                "localField": "estudiante.institucionEstudianteId",
                "foreignField": "_id",
                "as": "institucion"
            }
        },
        {"$unwind": "$institucion"},
        {
            "$match": {
                "institucion.nombreInstitucion": nombre_institucion
            }
        },
        {"$unwind": "$detalles_cobro"},
        {
            "$lookup": {
                "from": "cronograma_base",
                "let": {"detalleId": "$detalles_cobro._id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {"$in": ["$$detalleId", "$detalle_cobro._id"]}
                        }
                    }
                ],
                "as": "cronograma"
            }
        },
        {"$unwind": "$cronograma"},
        {
            "$project": {
                "monto_recibo": {"$toDouble": "$nmonto"},
                "mes": "$detalles_cobro.mes",
                "valor_detalle": {"$toDouble": "$detalles_cobro.valor"},
                "estudiante_id": {"$toString": "$estudiante._id"},
                "nombre_estudiante": "$estudiante.nombreEstudiante",
                "nombre_grado": "$cronograma.grado",
                "nombre_institucion": "$institucion.nombreInstitucion",
                "nombre_concepto": "$cronograma.nombre",
                "codigo": "$cronograma.codigo"
            }
        }
    ]
    print("Pipeline: ", pipeline)

    # Ejecutar el pipeline
    resultados = db["recibo_cobro"].aggregate(pipeline)

    # Convertir a lista
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




