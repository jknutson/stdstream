import datetime
import pika
import sys
import select
from config import config
from subprocess import check_output, Popen, PIPE, STDOUT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from stdstream.models import LogEntry, RsyncLog

class Publisher:
  def __init__(self, command=None):
    if command is None:
      self.command = ['cat', 'stdstream/testfile']
    else:
      self.command = command
    self.return_code = None
    self.rabbitmq_params = config['RABBITMQ_PARAMS']
    self.queue = 'stdout'

  def print_ouput(self, command):
    p = Popen(self.command, stdout=PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
      print line,
    p.communicate() # close p.stdout, wait for the subprocess to exit

  def yield_output(self):
    p = Popen(self.command, stdout=PIPE, stderr=STDOUT, bufsize=1)
    for line in iter(p.stdout.readline, b''):
      yield line,
    p.communicate() # close p.stdout, wait for the subprocess to exit

  def publish_message_queue(self, message, routing_key):
    with pika.BlockingConnection(self.rabbitmq_params) as connection:
      channel = connection.channel()
      channel.queue_declare(queue=self.queue)
      for line in self.yield_output():
        channel.basic_publish(exchange='',
                              routing_key=routing_key,
                              body=message)
        print " [x] Sent line"

  def publish_topic(self, message, exchange, routing_key):
    connection = pika.BlockingConnection(self.rabbitmq_params)
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange,
                             type='topic')
    channel.basic_publish(exchange=exchange,
                          routing_key=routing_key,
                          body=message)
    print " [x] sent %r:%r" % (routing_key, message)
    connection.close()

  def pre_exec(self):
    message = "%s STARTING: '%s'" % (datetime.datetime.now(), ' '.join(self.command))
    self.publish_topic(message, 'topic_logs', 'sys.info')

  def post_exec(self):
    message = "%s FINISHED: '%s' %s" % (datetime.datetime.now(), ' '.join(self.command), self.return_code)
    self.publish_topic(message, 'topic_logs', 'sys.info')

  def split_output(self):
    min_runtime = datetime.timedelta(seconds=20)
    start_time = datetime.datetime.now()
    self.pre_exec()
    p = Popen(self.command,
              stdout=PIPE,
              stderr=PIPE)
    stdout = []
    stderr = []
    while True:
      reads = [p.stdout.fileno(), p.stderr.fileno()]
      ret = select.select(reads, [], [])
      for fd in ret[0]:
        if fd == p.stdout.fileno():
          read = p.stdout.readline()
          if read != '':
            self.publish_topic(read, 'topic_logs', 'sys.stdout')
        if fd == p.stderr.fileno():
          read = p.stderr.readline()
          if read != '':
            self.publish_topic(read, 'topic_logs', 'sys.stderr')
      return_code = p.poll()
      if return_code != None and (datetime.datetime.now() - min_runtime > start_time):
        self.return_code = return_code
        self.post_exec()
        return return_code

  def publish_output_simple(self):
    with pika.BlockingConnection(self.rabbitmq_params) as connection:
      channel = connection.channel()
      channel.queue_declare(queue=self.queue)
      for line in self.yield_output():
        channel.basic_publish(exchange='',
                              routing_key=self.queue,
                              body=line[0])
        print " [x] Sent line"

class Subscriber:
  """ Represents an object for getting things from the Queue """

  def __init__(self):
    self.sqlalchemy_uri = config['SQLALCHEMY_URI']
    self.rabbitmq_params = config['RABBITMQ_PARAMS']
    self.queue = 'stdout'
    Session = sessionmaker(bind=create_engine(self.sqlalchemy_uri))
    self.session = Session()

  def callback(self, ch, method, properties, body):
    #self.session.add(LogEntry(data=body))
    #self.session.commit()
    print " [x] Received %r" % (body,)

  def rsync_topic_callback(self, ch, method, properties, body):
    print 'callback called'
    data = body.split('|')
    print data
    if len(data) > 4:
      timestamp = data[0]
      pid = data[1]
      itemized_changes = data[2]
      filename = data[3]
      bytes_transferred = data[4]
      l = RsyncLog(timestamp=timestamp,
                   pid=pid,
                   itemized_changes=itemized_changes,
                   filename=filename,
                   bytes_transferred=bytes_transferred)
      self.session.add(l)
      #self.session.commit()
      print " [x] commited %r" % data
    else:
      print 'weird data: %s' % body

  def callback_test(self, ch, method, properties, body):
    print body
    data = body.split('|')
    if len(data) > 4:
      print ' '.join(data)


  def consume_topic(self):
    exchange = 'topic_logs'
    queue = 'stdout'
    connection = pika.BlockingConnection(self.rabbitmq_params)
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange,
                             type='topic')
    #result = channel.queue_declare(exclusive=True)
    #queue = result.method.queue
    channel.queue_bind(exchange=exchange,
                       queue=queue,
                       routing_key='sys.stdout')
    channel.queue_declare(queue=queue)
    channel.basic_consume(self.rsync_topic_callback,
                          queue=queue,
                          no_ack=True)
    print "start consuming"
    channel.start_consuming()

  def consume_gen(self):
    exchange = 'topic_logs'
    queue =  'stdout'
    connection = pika.BlockingConnection(self.rabbitmq_params)
    channel = connection.channel()
    for method_frame, properties, body in channel.consume(queue=queue):
      #print method_frame
      #print properties
      #print body
      data = body.split('|')
      print data
      if len(data) > 4:
        timestamp = data[0]
        pid = data[1]
        itemized_changes = data[2]
        filename = data[3]
        bytes_transferred = data[4]
        l = RsyncLog(timestamp=timestamp,
                     pid=pid,
                     itemized_changes=itemized_changes,
                     filename=filename,
                     bytes_transferred=bytes_transferred)
        self.session.add(l)
        self.session.commit()
        print " [x] commited %r" % data


  def consume_messages(self):
    connection = pika.BlockingConnection(self.rabbitmq_params)
    channel = connection.channel()
    channel.queue_declare(queue=self.queue)
    channel.basic_consume(self.rsync_topic_callback,
                          queue=self.queue,
                          no_ack=True)
    channel.start_consuming()
