#!/usr/bin/env python
import os
import sys
import re
import subprocess
from collections import defaultdict

def raid_status():
  status = defaultdict(list)
  current = '' 

  file = open('/proc/mdstat', 'r')
  # lines = TEST.split("\n") 
  lines = file.readlines()
  file.close() 
  
  for l in lines:
    device = re.match('(md\d+) : (.*)', l)
    
    if re.match('Personalities : ', l):
      pass
    elif re.match('unused devices: ', l):
      pass
    elif not l.strip():
      pass
    elif device:
      name = device.group(1)
      detail = device.group(2)
      current = name  
      status[current].append(detail) 
    else:
      status[current].append(re.sub('^\s+', '', l))

  results = {}      
  for device, data in status.iteritems():
    array_status = data[0].split()[0]
    disk_status = data[1].split()[-1]
    
    up = [int((c == 'U')) for c in list(data[1].split()[-1][1:-1])]
    df = subprocess.Popen(
      ['/bin/df', '-m', '/dev/%s' % device], 
      stdout=subprocess.PIPE
    )
    
    usage = subprocess.Popen(
      ['grep', '/dev/%s' % device], 
      stdin=df.stdout,
      stdout=subprocess.PIPE
    ).communicate()[0].split()[4]
    
    results[device] = { 
      'active': array_status == 'active',
      'disk_up_pct': sum(up) / len(up) * 100,
      'usage_pct': int(re.search('(\d+)%', usage).group(1)),
    }
    
  return results
 
  
def firmware_version(): 
  installed = subprocess.Popen(
    ['/bin/zysh', '-e', 'show system fwversion'], 
    stdout=subprocess.PIPE
  ).communicate()[0]
  
  fwinfo = subprocess.Popen(
    ['/bin/zysh', '-e', 'zyfw get fwInfo 0'], 
    stdout=subprocess.PIPE
  )
  
  latest = subprocess.Popen(
    ['grep', 'version'], 
    stdin=fwinfo.stdout, 
    stdout=subprocess.PIPE
  ).communicate()[0]
  
  installed = re.search('.*: V(.*)\(.*\)', installed).group(1)
  latest = re.search('.*: V(.*)\(.*\)', latest).group(1)
  
  return {
    'installed': installed, 
    'latest': latest,
    'current': installed == latest
  }


def cpu_temp_c():
  temp = subprocess.Popen(
    ['/bin/zysh', '-e', 'enable; show cpu temperature'],
    stdout=subprocess.PIPE
  ).communicate()[0]
  
  return float(re.search('([+\-]\d+\.\d+) C', temp).group(1))
 
  
def cpu_usage_pct():
  usage = subprocess.Popen(
    ['/bin/zysh', '-e', 'show system cpuusage'], 
    stdout=subprocess.PIPE
  ).communicate()[0]
  
  result = re.search('CPU utilization: (\d+) %', usage).group(1)
  return int(result)

  
def fan_rpm():
  rpm = subprocess.Popen(
    ['/bin/zysh', '-e', 'enable; show fan-speed'],
    stdout=subprocess.PIPE
  ).communicate()[0]

  return int(re.search('speed: (\d+)', rpm).group(1))


def mem_used_pct():
  memory = subprocess.Popen(
    ['/bin/zysh', '-e', 'enable; show mem status'], 
    stdout=subprocess.PIPE
  ).communicate()[0].split("\n")

  mem_used_pct = re.search('(\d+)%', memory[2]).group(1)
    
  return int(mem_used_pct)

  
def smart_stats():
  pass

  
# send zyxel metrics to circonus
CIRCONUS_URL = 'https://trap.noit.circonus.net/module/httptrap/01234567-89ab-cdef-0123-456789abcdef/mys3cr3t'

# pull CIRCONUS_API_TOKEN from environment
try:
  CIRCONUS_API_TOKEN = os.environ['CIRCONUS_API_TOKEN']
except KeyError:
  print 'CIRCONUS_API_TOKEN is not set. Exiting.'
  sys.exit(1)

# set to True the metrics you want
METRICS = {
  'raid_status'       : True,
  'firmware_version'  : True,
  'cpu_temp_c'        : True,
  'cpu_usage_pct'     : True,
  'fan_rpm'           : True,
  'mem_used_pct'      : True,
  'smart_stats'       : False,
}

results = {}

# for each metric, collect & add to results dict
for metric, enabled in METRICS.iteritems():
  if enabled:
    result = { metric: locals()[metric]() }
    results.update(result)
   
jsondata = simplejson.dumps(results)
                                   
httptrapurl = os.environ['CIRCONUS_URL']
                  
# Form the PUT request      
requestHeaders = {"Accept": "application/json"}
req = urllib2.Request(httptrapurl, jsondata, headers = requestHeaders)
req.get_method = lambda: 'PUT'    
opener = urllib2.urlopen(req)
putresponse = simplejson.loads(opener.read())
              
# Print the data we get back to the screen so we can make sure it's working
print putresponse

