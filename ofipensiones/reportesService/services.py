from django.db.models import Q
from datetime import date, timedelta

from manejador_cronogramas.models import Curso, DetalleCobroCurso
from manejador_facturacion.models import ReciboCobro, ReciboPago


from django.db import connection

def obtener_cuentas_por_cobrar(nombre_institucion, mes):
    print("Hit the DB")
    query = """
    SELECT 
        rc.nmonto AS monto_recibo,
        dc.mes,
        dc.valor AS valor_detalle,
        rc.estudiante_id,
        es."nombreEstudiante" AS nombre_estudiante,
        c.grado AS nombre_grado,
        i."nombreInstitucion" AS nombre_institucion,
        cb.nombre AS nombre_concepto,
        cb.codigo
    FROM 
        public.manejador_facturacion_recibocobro rc
    JOIN 
        public.manejador_facturacion_recibocobro_detalles_cobro rcdc ON rc.id = rcdc.recibocobro_id
    JOIN 
        public.manejador_cronogramas_detallecobrocurso dc ON rcdc.detallecobrocurso_id = dc.id
    LEFT JOIN 
        public.manejador_facturacion_recibopago rp ON rc.id = rp.recibo_cobro_id
    JOIN 
        public.manejador_cronogramas_estudiante es ON rc.estudiante_id = es.id
    JOIN 
        public.manejador_cronogramas_curso c ON es."cursoEstudiante_id" = c.id
    JOIN 
        public.manejador_cronogramas_institucion i ON c.institucion_id = i.id
    JOIN 
        public.manejador_cronogramas_cronogramabase cb ON dc.cronograma_curso_id = cb.id
    WHERE
        i."nombreInstitucion" = %s AND
        dc.mes = %s AND
        rp.id IS NULL;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [nombre_institucion, mes])
        rows = cursor.fetchall()

    # Convertir los valores a un formato más legible
    processed_rows = [
        {
            "monto_recibo": float(row[0]),  # monto_recibo
            "mes": row[1],                   # mes
            "valor_detalle": float(row[2]),  # valor_detalle
            "estudiante_id": row[3],         # estudiante_id
            "nombre_estudiante": row[4],     # nombre_estudiante
            "nombre_grado": row[5],          # nombre_grado
            "nombre_institucion": row[6],    # nombre_institucion
            "nombre_concepto": row[7],       # nombre_concepto
            "codigo": row[8]                 # codigo
        }
        for row in rows
    ]

    return processed_rows


def obtener_cartera_general(nombre_institucion, mes):
    print("Hit the DB")
    query = """
    SELECT 
    SUM(rc.nmonto) AS total_deuda
    FROM 
        public.manejador_facturacion_recibocobro rc
    JOIN 
        public.manejador_facturacion_recibocobro_detalles_cobro rcdc ON rc.id = rcdc.recibocobro_id
    JOIN 
        public.manejador_cronogramas_detallecobrocurso dc ON rcdc.detallecobrocurso_id = dc.id
    LEFT JOIN 
        public.manejador_facturacion_recibopago rp ON rc.id = rp.recibo_cobro_id
    JOIN 
        public.manejador_cronogramas_estudiante es ON rc.estudiante_id = es.id
    JOIN 
        public.manejador_cronogramas_curso c ON es."cursoEstudiante_id" = c.id
    JOIN 
        public.manejador_cronogramas_institucion i ON c.institucion_id = i.id
    JOIN 
        public.manejador_cronogramas_cronogramabase cb ON dc.cronograma_curso_id = cb.id
    WHERE
        i."nombreInstitucion" = %s AND
        dc.mes = %s AND
        rp.id IS NULL;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [nombre_institucion, mes])
        rows = cursor.fetchall()

    # Convertir los valores a un formato más legible
    processed_rows = [
        {
            "institucion": nombre_institucion,
            "mes": mes,
            "total_deuda": float(row[0]) if row[0] is not None else 0.0  # Manejar None
        }
        for row in rows
    ]

    return processed_rows


