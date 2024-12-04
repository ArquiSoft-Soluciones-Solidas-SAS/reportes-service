from reportesService.models import Institucion, Curso, Estudiante, CronogramaBase, DetalleCobroCurso, \
    ReciboCobro, ReciboPago
import json
import pika
from sys import path
from os import environ
import django
import sys
from datetime import datetime

rabbit_host = '10.142.0.12'
rabbit_user = 'microservicios_user'
rabbit_password = 'password'
exchange = 'instituciones'
# Lista de intercambios y temas
exchanges_and_topics = {
    'recibos_pago': ['recibo.pago.created'],
    'recibos_cobro': ['recibo.cobro.created'],
    'cronogramas': ['cronograma.created'],
    'estudiantes': ['estudiante.created'],
    'instituciones': ['institucion.created']
}

# Añadir el directorio donde está el proyecto 'ofipensiones' al sys.path
# Esta es la ruta donde está el directorio de tu proyecto
sys.path.append('/labs/reportes-service/ofipensiones')

# Configurar el entorno de Django para que use el archivo settings.py
environ.setdefault('DJANGO_SETTINGS_MODULE', 'ofipensiones.settings')

django.setup()


# Callback genérico para recibir y procesar mensajes

def callback(ch, method, properties, body):
    message = json.loads(body)
    print(
        f"Received message from {method.exchange} [{method.routing_key}]: {message}")

    # Procesar según el intercambio
    if method.exchange == 'instituciones' and method.routing_key == 'institucion.created':
        # Obtener los datos de la institución
        institucion_data = message.get("data")
        institucion_id = institucion_data.get("id")

        # Intentar obtener la institución existente, si existe
        institucion, created = Institucion.objects.update_or_create(
            id=institucion_id,
            defaults={
                'nombreInstitucion': institucion_data.get("nombreInstitucion"),
            }
        )

        # Si la institución es nueva, añadimos los cursos
        if created:
            # Solo se añaden los cursos si la institución es nueva
            institucion.cursos.set(
                [Curso(
                    id=curso.get("id"),
                    grado=curso.get("grado"),
                    numero=curso.get("numero"),
                    anio=curso.get("anio")
                ) for curso in institucion_data.get("cursos")]
            )
        else:
            # Si la institución ya existía, puedes actualizar sus cursos si es necesario
            institucion.cursos.clear()
            institucion.cursos.set(
                [Curso(
                    id=curso.get("id"),
                    grado=curso.get("grado"),
                    numero=curso.get("numero"),
                    anio=curso.get("anio")
                ) for curso in institucion_data.get("cursos")]
            )

        # Guardar la institución
        institucion.save()

    elif method.exchange == 'estudiantes' and method.routing_key == 'estudiante.created':
        # Obtener los datos del estudiante
        estudiante_data = message.get("data")
        estudiante_id = estudiante_data.get("id")
        # Intentar obtener el estudiante existente o crear uno nuevo
        estudiante, created = Estudiante.objects.update_or_create(
            id=estudiante_id,
            defaults={
                'nombreEstudiante': estudiante_data.get("nombreEstudiante"),
                'codigoEstudiante': estudiante_data.get("codigoEstudiante"),
                'institucionEstudianteId': estudiante_data.get("institucionEstudianteId"),
                'nombreInstitucion': estudiante_data.get("nombreInstitucion"),
                'cursoEstudianteId': estudiante_data.get("cursoEstudianteId"),
            }
        )
        # Guardar el estudiante
        estudiante.save()

    elif method.exchange == 'cronogramas' and method.routing_key == 'cronograma.created':

        # Obtener los datos del cronograma
        cronograma_data = message.get("data")
        cronograma_id = cronograma_data.get("id")

        # Intentar obtener el cronograma existente o crear uno nuevo
        cronograma, created = CronogramaBase.objects.update_or_create(
            id=cronograma_id,
            defaults={
                'institucionId': cronograma_data.get("institucionId"),
                'nombreInstitucion': cronograma_data.get("nombreInstitucion"),
                'cursoId': cronograma_data.get("cursoId"),
                'grado': cronograma_data.get("grado"),
                'codigo': cronograma_data.get("codigo"),
                'nombre': cronograma_data.get("nombre"),
            }
        )

        # Actualizar los detalles de cobro
        if created:
            cronograma.detalle_cobro.set(
                [DetalleCobroCurso(
                    id=detalle.get("id"),
                    mes=detalle.get("mes"),
                    valor=detalle.get("valor"),
                    fechaCausacion=detalle.get("fechaCausacion"),
                    fechaLimite=detalle.get("fechaLimite"),
                    frecuencia=detalle.get("frecuencia")
                ) for detalle in cronograma_data.get("detalle_cobro")]
            )
        else:
            cronograma.detalle_cobro.clear()
            cronograma.detalle_cobro.set(
                [DetalleCobroCurso(
                    id=detalle.get("id"),
                    mes=detalle.get("mes"),
                    valor=detalle.get("valor"),
                    fechaCausacion=detalle.get("fechaCausacion"),
                    fechaLimite=detalle.get("fechaLimite"),
                    frecuencia=detalle.get("frecuencia")
                ) for detalle in cronograma_data.get("detalle_cobro")]
            )
        cronograma.save()

    elif method.exchange == 'recibos_cobro' and method.routing_key == 'recibo.cobro.created':

        # Obtener los datos del recibo de cobro
        recibo_data = message.get("data")
        recibo_id = recibo_data.get("id")

        # Intentar obtener el recibo de cobro existente o crear uno nuevo
        recibo, created = ReciboCobro.objects.update_or_create(
            id=recibo_id,
            defaults={
                'fecha': recibo_data.get("fecha"),
                'nmonto': recibo_data.get("nmonto"),
                'detalle': recibo_data.get("detalle"),
                'estudianteId': recibo_data.get("estudianteId"),
            }
        )
        # Actualizar los detalles de cobro
        if created:
            recibo.detalles_cobro.set(
                [DetalleCobroCurso(
                    id=detalle.get("id"),
                    mes=detalle.get("mes"),
                    valor=detalle.get("valor"),
                    fechaCausacion=detalle.get("fechaCausacion"),
                    fechaLimite=detalle.get("fechaLimite"),
                    frecuencia=detalle.get("frecuencia")
                ) for detalle in recibo_data.get("detalles_cobro")]
            )
        else:
            recibo.detalles_cobro.clear()
            recibo.detalles_cobro.set(
                [DetalleCobroCurso(
                    id=detalle.get("id"),
                    mes=detalle.get("mes"),
                    valor=detalle.get("valor"),
                    fechaCausacion=detalle.get("fechaCausacion"),
                    fechaLimite=detalle.get("fechaLimite"),
                    frecuencia=detalle.get("frecuencia")
                ) for detalle in recibo_data.get("detalles_cobro")]
            )
        recibo.save()

    elif method.exchange == 'recibos_pago' and method.routing_key == 'recibo.pago.created':

        # Obtener los datos del recibo de pago
        recibo_pago_data = message.get("data")
        recibo_pago_id = recibo_pago_data.get("id")
        # Intentar obtener el recibo de pago existente o crear uno nuevo
        recibo_pago, created = ReciboPago.objects.update_or_create(
            id=recibo_pago_id,
            defaults={
                'fecha': recibo_pago_data.get("fecha"),
                'nmonto': recibo_pago_data.get("nmonto"),
                'detalle': recibo_pago_data.get("detalle"),
            }
        )
        # Obtener o crear el recibo de cobro asociado
        recibo_cobro_data = recibo_pago_data.get("recibo_cobro")
        recibo_cobro, cobro_created = ReciboCobro.objects.update_or_create(
            id=recibo_cobro_data.get("id"),
            defaults={
                'fecha': recibo_cobro_data.get("fecha"),
                'nmonto': recibo_cobro_data.get("nmonto"),
                'detalle': recibo_cobro_data.get("detalle"),
                'estudianteId': recibo_cobro_data.get("estudianteId"),
            }
        )
        recibo_pago.recibo_cobro = recibo_cobro
        recibo_pago.save()


# Conexión a RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=rabbit_host,
        credentials=pika.PlainCredentials(rabbit_user, rabbit_password)
    )
)
channel = connection.channel()

# Configurar intercambios, colas y bindings
for exchange, topics in exchanges_and_topics.items():
    # Declarar el intercambio
    channel.exchange_declare(exchange=exchange, exchange_type='topic')

    # Crear una cola exclusiva para este cliente
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    # Vincular la cola al intercambio con los temas especificados
    for topic in topics:
        channel.queue_bind(exchange=exchange,
                           queue=queue_name, routing_key=topic)

    # Suscribirse a la cola
    channel.basic_consume(
        queue=queue_name, on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages from multiple exchanges. To exit press CTRL+C')
channel.start_consuming()
