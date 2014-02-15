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


def memoize(f):
  """ Memoization decorator for functions taking one or more arguments. """
  class memodict(dict):
    def __init__(self, f):
      self.f = f
    def __call__(self, *args):
      return self[args]
    def __missing__(self, key):
      ret = self[key] = self.f(*key)
      return ret
  return memodict(f)

@memoize
def mpq(url):
  return pq(url=url)

def list_episodes_youku(title_url):
  output = []
  youku_parts = list_youku_parts(title_url)
  if len(youku_parts) > 0:
    for part in youku_parts:
      output.extend(list_episodes_in_youku_part(part))
    return output
  d = mpq(title_url)
  for x in d('.seriespanels').find('a'):
    episode = pq(x)
    text = episode.text()
    print('text:', text)
    if text != str(len(output) + 1):
      print('skipping:', text)
      continue
    href = episode.attr('href')
    output.append(href)
  return output

def list_episodes_soku(title_url):
  output = []
  d = mpq(title_url)
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
  d = mpq(title_url)
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
    for trynum in range(2):
      if trynum > 0:
        print('retrying, episode_num:', episode_num, 'trynum:', trynum)
      if os.path.exists(tmpdir):
        print('removing tmpdir:', tmpdir)
        rmtree(tmpdir)
      command = ['you-get', '-o', tmpdir] + opt_args + [episode_url]
      print(' '.join(command))
      call(command)
      tmpdir_files = [x for x in os.listdir(tmpdir) if not x.startswith('.')]
      if len(tmpdir_files) == 1:
        break # success
      else:
        print('tmpdir_files not correct:', tmpdir, tmpdir_files)
    move(tmpdir + '/' + tmpdir_files[0], output_file)
    rmtree(tmpdir)



def youku_series_id_from_url(url):
  assert 'http://www.youku.com/show_page/id_' in url
  return url.replace('http://www.youku.com/show_page/id_', '').replace('.html', '')

def youku_jsload_geturl(partname, series_id):
  return 'http://www.youku.com/show_episode/id_' + series_id + '.html?dt=json&divid=' + partname

def list_episodes_in_youku_part(part_url):
  output = []
  d = mpq(part_url)
  for x in d.find('a'):
    output.append(d(x).attr('href'))
  return output

def list_youku_parts(url):
  series_id = youku_series_id_from_url(url)
  output = []
  d = mpq(url)
  for x in d('#reload_showInfo').find('a'):
    reloadPanelLink = pq(x)
    onclick = reloadPanelLink.attr('onclick')
    if onclick and 'y.episode.show(' in onclick:
      link = onclick.replace('y.episode.show(\'', '').replace('\')', '')
      output.append(youku_jsload_geturl(link, series_id))
  return output


if __name__ == '__main__':
  main()


