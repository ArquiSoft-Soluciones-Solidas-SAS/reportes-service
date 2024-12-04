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
sys.path.append('/labs/reportes-service/ofipensiones')  # Esta es la ruta donde está el directorio de tu proyecto

# Configurar el entorno de Django para que use el archivo settings.py
environ.setdefault('DJANGO_SETTINGS_MODULE', 'ofipensiones.settings')

django.setup()

from reportesService.models import Institucion, Curso, Estudiante, CronogramaBase, DetalleCobroCurso, \
    ReciboCobro, ReciboPago

# Callback genérico para recibir y procesar mensajes
def callback(ch, method, properties, body):
    message = json.loads(body)
    print(f"Received message from {method.exchange} [{method.routing_key}]: {message}")

    # Procesar según el intercambio
    if method.exchange == 'instituciones' and method.routing_key == 'institucion.created':
        # Guardar en la base de datos Institucion
        institucion_data = message.get("data")
        Institucion.objects(id=institucion_data.get("id")).update(
            set__nombreInstitucion=institucion_data.get("nombreInstitucion"),
            set__cursos=[Curso(
                id=curso.get("id"),
                grado=curso.get("grado"),
                numero=curso.get("numero"),
                anio=curso.get("anio")
            ) for curso in institucion_data.get("cursos")],
            upsert=True
        )

    elif method.exchange == 'estudiantes' and method.routing_key == 'estudiante.created':
        # Guardar en la base de datos Estudiante
        estudiante_data = message.get("data")
        estudiante = Estudiante(
            id=estudiante_data.get("id"),
            nombreEstudiante=estudiante_data.get("nombreEstudiante"),
            codigoEstudiante=estudiante_data.get("codigoEstudiante"),
            institucionEstudianteId=estudiante_data.get("institucionEstudianteId"),
            nombreInstitucion=estudiante_data.get("nombreInstitucion"),
            cursoEstudianteId=estudiante_data.get("cursoEstudianteId")
        )
        estudiante.save()

    elif method.exchange == 'cronogramas' and method.routing_key == 'cronograma.created':
        # Guardar en la base de datos CronogramaBase
        cronograma_data = message.get("data")
        cronograma = CronogramaBase(
            id=cronograma_data.get("id"),
            institucionId=cronograma_data.get("institucionId"),
            nombreInstitucion=cronograma_data.get("nombreInstitucion"),
            cursoId=cronograma_data.get("cursoId"),
            grado=cronograma_data.get("grado"),
            codigo=cronograma_data.get("codigo"),
            nombre=cronograma_data.get("nombre"),
            detalle_cobro=[DetalleCobroCurso(
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
        # Guardar en la base de datos ReciboCobro
        recibo_data = message.get("data")
        recibo = ReciboCobro(
            id=recibo_data.get("id"),
            fecha=recibo_data.get("fecha"),
            nmonto=recibo_data.get("nmonto"),
            detalle=recibo_data.get("detalle"),
            estudianteId=recibo_data.get("estudianteId"),
            detalles_cobro=[DetalleCobroCurso(
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
        # Guardar en la base de datos ReciboPago
        recibo_pago_data = message.get("data")
        recibo_pago = ReciboPago(
            id=recibo_pago_data.get("id"),
            fecha=recibo_pago_data.get("fecha"),
            nmonto=recibo_pago_data.get("nmonto"),
            detalle=recibo_pago_data.get("detalle"),
            recibo_cobro=ReciboCobro(
                id=recibo_pago_data.get("recibo_cobro").get("id"),
                fecha=recibo_pago_data.get("recibo_cobro").get("fecha"),
                nmonto=recibo_pago_data.get("recibo_cobro").get("nmonto"),
                detalle=recibo_pago_data.get("recibo_cobro").get("detalle"),
                estudianteId=recibo_pago_data.get("recibo_cobro").get("estudianteId"),
                detalles_cobro=[DetalleCobroCurso(
                    id=detalle.get("id"),
                    mes=detalle.get("mes"),
                    valor=detalle.get("valor"),
                    fechaCausacion=detalle.get("fechaCausacion"),
                    fechaLimite=detalle.get("fechaLimite"),
                    frecuencia=detalle.get("frecuencia")
                ) for detalle in recibo_pago_data.get("recibo_cobro").get("detalles_cobro")]
            )
        )
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
        channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=topic)

    # Suscribirse a la cola
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages from multiple exchanges. To exit press CTRL+C')
channel.start_consuming()