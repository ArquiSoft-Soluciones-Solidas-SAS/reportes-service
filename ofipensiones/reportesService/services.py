from django.db.models import Q
from datetime import date, timedelta

from django.http import JsonResponse
from pymongo import MongoClient

from .models import Curso, DetalleCobroCurso, ReciboCobro, ReciboPago, Institucion, Estudiante, CronogramaBase
from mongoengine import Q


def obtener_cuentas_por_cobrar(nombre_institucion, mes):
    # 1. Filtrar cronogramas base por institución y obtener IDs relevantes
    cronogramas = CronogramaBase.objects(nombreInstitucion=nombre_institucion)
    curso_ids = [cronograma.cursoId for cronograma in cronogramas]

    # 2. Filtrar estudiantes por institución y cursos
    estudiantes = Estudiante.objects(
        Q(nombreInstitucion=nombre_institucion) & Q(cursoEstudianteId__in=curso_ids)
    )

    # 3. Obtener recibos de cobro de los estudiantes y filtrar por mes en detalles_cobro
    recibos = ReciboCobro.objects(
        Q(estudiante__in=[estudiante.id for estudiante in estudiantes]) &
        Q(detalles_cobro__mes=mes)
    )

    cuentas_por_cobrar = []

    for recibo in recibos:
        # Calcular el monto total del recibo
        monto_total = sum(detalle.valor for detalle in recibo.detalles_cobro if detalle.mes == mes)

        # Obtener pagos realizados para este recibo
        pagos = ReciboPago.objects(recibo_cobro=recibo)

        # Calcular el monto pagado
        monto_pagado = sum(pago.nmonto for pago in pagos)

        # Calcular saldo pendiente
        saldo_pendiente = monto_total - monto_pagado

        # Construir el resultado
        cuentas_por_cobrar.append({
            "monto_recibo": monto_total,
            "mes": mes,
            "valor_detalle": saldo_pendiente,
            "estudiante_id": recibo.estudiante,
            "nombre_estudiante": next(
                (e.nombreEstudiante for e in estudiantes if e.id == recibo.estudiante),
                "Desconocido"
            ),
            "nombre_grado": next(
                (c.grado for c in cronogramas if c.cursoId in curso_ids),
                "Desconocido"
            ),
            "nombre_institucion": nombre_institucion,
            "nombre_concepto": recibo.detalle,
            "codigo": recibo.id,
        })

    return cuentas_por_cobrar




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




