import pika

config = {}

RABBITMQ_HOST='localhost'
RABBITMQ_VHOST='/stdstream'
RABBITMQ_QUEUE='stdout'
RABBITMQ_USER='stdstream'
RABBITMQ_PASS='stdstream'
RABBITMQ_CREDENTIALS=pika.PlainCredentials(RABBITMQ_USER,
                                           RABBITMQ_PASS)
RABBITMQ_PARAMS=pika.ConnectionParameters(host=RABBITMQ_HOST,
                                          virtual_host=RABBITMQ_VHOST,
                                          credentials=RABBITMQ_CREDENTIALS)

SQLALCHEMY_URI = 'mysql://stdstream:stdstream@192.168.11.3/stdstream'


config['RABBITMQ_PARAMS'] = RABBITMQ_PARAMS
config['SQLALCHEMY_URI'] = SQLALCHEMY_URI
