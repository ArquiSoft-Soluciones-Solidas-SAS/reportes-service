import json
import pika
from sys import path
from os import environ
import django
import sys

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


# Callback genérico para recibir y procesar mensajes
def callback(ch, method, properties, body):
    message = json.loads(body)
    print(f"Received message from {method.exchange} [{method.routing_key}]: {message}")
    # Aquí puedes guardar la información en tu base de datos NoSQL


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