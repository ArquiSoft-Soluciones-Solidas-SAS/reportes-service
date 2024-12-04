from django.db.models import Q
from datetime import date, timedelta

from .models import Curso, DetalleCobroCurso, ReciboCobro, ReciboPago, Institucion, Estudiante, CronogramaBase

from django.db import connection

from mongoengine.queryset.visitor import Q

from django.http import JsonResponse
from decimal import Decimal
from mongoengine.queryset.visitor import Q


from django.http import JsonResponse
from django.db.models import Q

from django.http import JsonResponse
from django.db.models import Q

def obtener_cuentas_por_cobrar(nombre_institucion, mes):
    """
    Obtiene las cuentas por cobrar para una institución en un mes específico.
    """
    print("Hit the DB")
    print("Ejecutando la función..., con los parámetros: ", nombre_institucion, mes)

    try:
        # Filtrar cronogramas base de la institución
        cronogramas = CronogramaBase.objects.filter(
            nombreInstitucion=nombre_institucion
        ).only("id", "detalle_cobro")

        # Filtrar estudiantes de la institución
        estudiantes = Estudiante.objects.filter(
            nombreInstitucion=nombre_institucion
        ).only("id", "cursoEstudianteId", "nombreEstudiante")

        # Filtrar recibos de cobro asociados a los estudiantes y al mes
        recibos = ReciboCobro.objects.filter(
            estudiante__in=estudiantes,
            detalles_cobro__mes=mes
        ).only("id", "nmonto", "detalles_cobro", "estudiante")

        # Identificar los recibos que ya tienen pagos asociados
        recibos_pagados = ReciboPago.objects.filter(
            recibo_cobro__in=recibos
        )

        # Extraer los IDs de los recibos pagados
        recibos_pagados_ids = [recibo.recibo_cobro.id for recibo in recibos_pagados]

        # Filtrar los recibos que aún no han sido pagados
        recibos_no_pagados = recibos.exclude(id__in=recibos_pagados_ids)

        processed_rows = []

        for recibo in recibos_no_pagados:
            estudiante = Estudiante.objects.get(id=recibo.estudiante)
            curso = Curso.objects.get(id=estudiante.cursoEstudianteId)

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
        print(f"Error al obtener cuentas por cobrar: {e}")
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




