#!/usr/bin/env python3

# A script to download a series from youku.
# Github: http://github.com/gkovacs/youku_series
# Author: Geza Kovacs http://gkovacs.github.com

# Prereqs:
# Requires you-get to be installed beforehand.

# Usage example:
# ~/youku_series/youku_series.py -u http://www.youku.com/show_page/id_zcbfce0fc962411de83b1.html --sogou
# ~/youku_series/youku_series.py --url http://www.soku.com/detail/show/XMjI5ODcy --sogou --start 130 --end 135

import argparse
from pyquery import PyQuery as pq
from subprocess import call
import os
from shutil import move
from shutil import rmtree

def list_episodes_youku(title_url):
  output = []
  d = pq(url=title_url)
  for x in d('.seriespanels').find('a'):
    episode = pq(x)
    text = episode.text()
    if text != str(len(output) + 1):
      print('skipping:', text)
      continue
    href = episode.attr('href')
    output.append(href)
  return output

def list_episodes_soku(title_url):
  output = []
  d = pq(url=title_url)
  for linkpanels_xml in d('.linkpanels'):
    linkpanels = pq(linkpanels_xml)
    css = linkpanels.attr('style')
    css = ''.join(c for c in css)
    if 'display:none' in css:
      continue
    for linkpanel_xml in linkpanels.find('ul.linkpanel'):
      linkpanel = pq(linkpanel_xml)
      for episode_xml in linkpanel.find('a'):
        episode = pq(episode_xml)
        text = episode.text()
        if text != str(len(output) + 1):
          print('skipping:', text)
          continue
        href = episode.attr('href')
        output.append(href)
  return output


# returns a list of URLs to episodes
# title_url: ex: http://www.youku.com/show_page/id_zcbfce0fc962411de83b1.html
def list_episodes(title_url):
  if 'youku.com' in title_url:
    return list_episodes_youku(title_url)
  if 'soku.com' in title_url:
    return list_episodes_soku(title_url)

# returns the title of the show
# title_url: ex: http://www.youku.com/show_page/id_zcbfce0fc962411de83b1.html
def list_title(title_url):
  d = pq(url=title_url)
  # youku
  for x in d('h1.title').find('span.name'):
    return d(x).text()
  # soku
  for x in d('li.base_name').find('h1'):
    return d(x).text()

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-u', '--url')
  parser.add_argument('-t', '--title')
  parser.add_argument('-s', '--start', type=int)
  parser.add_argument('-e', '--end', type=int)
  parser.add_argument('-m', '--mock', action='store_true')
  args,opt_args = parser.parse_known_args()
  url = args.url
  if not url:
    if os.path.exists('series_url.txt'):
      url = open('series_url.txt').read().strip()
    else:
      print('need --url argument')
      return
  print('url:', url)
  title = args.title
  if not title:
    title = list_title(url)
  print('title:', title)
  if os.getcwd().split('/')[-1].strip() != title: # not already in title directory
    if not os.path.exists(title):
      os.makedirs(title)
    os.chdir(title)
  if not os.path.exists('series_url.txt'):
    open('series_url.txt', 'w').write(url)
  episode_list = list_episodes(url)
  start = args.start
  if not start:
    start = 1
  print('start:', start)
  end = args.end
  if not end:
    end = len(episode_list)
  print('end:', end)
  print('args:', opt_args)
  for episode_idx,episode_url in enumerate(episode_list):
    episode_num = episode_idx + 1
    if not start <= episode_num <= end:
      print('skipping:', episode_num)
      continue
    print(episode_num, ':', episode_url)
    if args.mock:
      continue
    output_file = str(episode_num) + '.mp4'
    if os.path.exists(output_file):
      print('already exists:', output_file)
      continue
    tmpdir = 'tmp_' + str(episode_num)
    if os.path.exists(tmpdir):
      print('removing tmpdir:', tmpdir)
      rmtree(tmpdir)
    call(['you-get', '-o', tmpdir] + opt_args + [episode_url])
    tmpdir_files = [x for x in os.listdir(tmpdir) if not x.startswith('.')]
    if len(tmpdir_files) != 1:
      print('tmpdir_files not correct:', tmpdir, tmpdir_files)
      return
    move(tmpdir + '/' + tmpdir_files[0], output_file)
    rmtree(tmpdir)

if __name__ == '__main__':
  main()
