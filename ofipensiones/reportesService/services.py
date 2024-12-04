from django.db.models import Q
from datetime import date, timedelta

from .models import Curso, DetalleCobroCurso, ReciboCobro, ReciboPago, Institucion, Estudiante, CronogramaBase

from django.db import connection

from mongoengine.queryset.visitor import Q

from django.http import JsonResponse
from decimal import Decimal
from mongoengine.queryset.visitor import Q


def obtener_cuentas_por_cobrar(request, nombre_institucion, mes):
    print("Hit the DB")
    print("Ejecutando la función..., con los parámetros: ", nombre_institucion, mes)
    try:
        # Obtener los recibos de cobro no pagados
        recibos_pagados_ids = ReciboPago.objects.distinct("recibo_cobro")

        recibos = ReciboCobro.objects.filter(
            Q(detalles_cobro__mes=mes) &
            Q(id__nin=recibos_pagados_ids)
        )

        processed_rows = []

        for recibo in recibos:
            # Obtener el estudiante relacionado
            estudiante = Estudiante.objects.get(id=recibo.estudiante)

            # Validar institución
            if estudiante.nombreInstitucion != nombre_institucion:
                continue

            # Obtener el curso relacionado
            curso = Curso.objects.get(id=estudiante.cursoEstudianteId)

            # Obtener el cronograma relacionado
            for detalle in recibo.detalles_cobro:
                if detalle.mes == mes:
                    cronograma = CronogramaBase.objects.get(detalle_cobro__id=detalle.id)

                    processed_rows.append({
                        "monto_recibo": float(recibo.nmonto),
                        "mes": detalle.mes,
                        "valor_detalle": float(detalle.valor),
                        "estudiante_id": str(estudiante.id),
                        "nombre_estudiante": estudiante.nombreEstudiante,
                        "nombre_grado": curso.grado,
                        "nombre_institucion": nombre_institucion,
                        "nombre_concepto": cronograma.nombre,
                        "codigo": cronograma.codigo
                    })

        return JsonResponse(processed_rows, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


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




