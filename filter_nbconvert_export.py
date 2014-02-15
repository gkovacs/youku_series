#!/usr/bin/env python3

import sys

atStart = True
inInput = True
postBlock = False
for line in sys.stdin:
  if line.startswith('# In['):
    inInput = True
    postBlock = True
    continue
  if line.startswith('# Out['):
    inInput = False
    postBlock = True
    continue
  if not inInput:
    continue
  if line.startswith('# noexport'):
    inInput = False
    continue
  if postBlock:
    postBlock = False
    continue
  if atStart:
    if line.strip() == '':
      continue
    else:
      atStart = False
  print(line, end='')