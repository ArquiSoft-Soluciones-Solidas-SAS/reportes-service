import json
import pika
from sys import path
from os import environ
#import django

rabbit_host = '10.142.0.12'
rabbit_user = 'microservicios_user'
rabbit_password = 'password'
exchange = 'instituciones'
topics = ['institucion.#']

# path.append('../ofipensiones/settings.py')
# environ.setdefault('DJANGO_SETTINGS_MODULE', 'ofipensiones.settings')
# django.setup()


def callback(ch, method, properties, body):
    message = json.loads(body)
    print(f"Received message: {message}")
    # Aquí puedes guardar la información en tu base de datos NoSQL


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbit_host, credentials=pika.PlainCredentials(rabbit_user, rabbit_password)))
channel = connection.channel()
channel.exchange_declare(exchange=exchange, exchange_type='topic')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange=exchange, queue=queue_name,
                   routing_key='institucion.created')

print(' [*] Waiting for logs. To exit press CTRL+C')
channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()
