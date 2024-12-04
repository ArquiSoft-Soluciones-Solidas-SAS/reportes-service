from django.db.models import Q
from datetime import date, timedelta

from .models import Curso, DetalleCobroCurso, ReciboCobro, ReciboPago, Institucion, Estudiante, CronogramaBase

from django.db import connection

from mongoengine.queryset.visitor import Q


def obtener_cuentas_por_cobrar(nombre_institucion, mes):
    print("Hit the DB")

    # Filtrar los cronogramas base de la institución
    cronogramas = CronogramaBase.objects.filter(
        nombreInstitucion=nombre_institucion
    ).only("id", "detalle_cobro", "nombre")

    processed_rows = []

    for cronograma in cronogramas:
        # Filtrar los detalles del cronograma para el mes especificado
        detalles_mes = [detalle for detalle in cronograma.detalle_cobro if detalle.mes == mes]
        for detalle_cobro in detalles_mes:
            # Buscar los recibos de cobro relacionados con este detalle
            recibos = ReciboCobro.objects.filter(
                detalles_cobro__id=detalle_cobro.id,
                id__nin=ReciboPago.objects.distinct("recibo_cobro")  # Recibos no pagados
            ).only("nmonto", "detalles_cobro", "estudiante")

            for recibo in recibos:
                # Obtener el objeto Estudiante relacionado
                estudiante = Estudiante.objects.get(id=recibo.estudiante.id)

                # Filtrar por institución del estudiante
                if estudiante.nombreInstitucion != nombre_institucion:
                    continue

                # Obtener el curso del estudiante
                curso = Curso.objects.get(id=estudiante.cursoEstudianteId)

                # Procesar los datos para la salida
                processed_rows.append({
                    "monto_recibo": float(recibo.nmonto),
                    "mes": detalle_cobro.mes,
                    "valor_detalle": float(detalle_cobro.valor),
                    "estudiante_id": str(estudiante.id),
                    "nombre_estudiante": estudiante.nombreEstudiante,
                    "nombre_grado": curso.grado,
                    "nombre_institucion": nombre_institucion,
                    "nombre_concepto": cronograma.nombre,
                    "codigo": cronograma.codigo
                })

    return processed_rows


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




