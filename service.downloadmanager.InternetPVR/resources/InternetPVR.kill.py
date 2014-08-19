#!/usr/bin/env python

import subprocess, signal
import os
import xbmc

p = subprocess.Popen(['ps', '-w'], stdout=subprocess.PIPE)
out, err = p.communicate()

for line in out.splitlines():
   if 'SickBeard.py' in line:
      pid = int(line.split(None, 1)[0])
      os.kill(pid, signal.SIGKILL)
      xbmc.log('InternetPVR: Shutting SickBeard down...', level=xbmc.LOGDEBUG)
   if 'CouchPotato.py' in line:
      pid = int(line.split(None, 1)[0])
      os.kill(pid, signal.SIGKILL)
      xbmc.log('InternetPVR: Shutting CouchPotato down...', level=xbmc.LOGDEBUG)
   if 'Headphones.py' in line:
      pid = int(line.split(None, 1)[0])
      os.kill(pid, signal.SIGKILL)
      xbmc.log('InternetPVR: Shutting Headphones down...', level=xbmc.LOGDEBUG)
