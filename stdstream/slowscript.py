#!/usr/bin/python
import sys
import time
import datetime

delay = 1
count = 10

if len(sys.argv) > 1:
  delay = int(sys.argv[1])
sys.stdout.write('stdout begin\n\n')
sys.stderr.write('stderr start\n\n')
for i in range(0,count):
  sys.stdout.write('stdout %s %s\n' % (i, datetime.datetime.now().time()))
  sys.stderr.write('stderr %s %s\n' % (i, datetime.datetime.now().time()))
  time.sleep(delay)


sys.stdout.write('\nstdout complete\n')
sys.stderr.write('\nstderr all done\n')

sys.exit(0)
