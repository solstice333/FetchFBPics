from urllib.parse import urlparse

import urllib.request
import re
import argparse
import os.path
import ssl


class URLFileParser:
   def __init__(self, file):
      self._file = open(file)

   def close(self):
      self._file.close()

   def get_urls(self):
      urls = []
      for line in self._file:
         for url in re.finditer(r'http\S+', line):
            urls.append(url.group(0))
      return urls

   def __enter__(self):
      return self

   def __exit__(self, *_):
      self.close()

   def __del__(self):
      self.close()

class Downloadable:
   def __init__(self, url):
      self._url = url
      self._url_parts = urlparse(self._url)
      self._default_filename = os.path.basename(self._url_parts.path)

   def download(self, dst='.', custom_filename=None):
      dst_path = os.path.realpath(
         os.path.join(dst, custom_filename or self._default_filename))
      with \
         urllib.request.urlopen(self._url, context=ssl.SSLContext()) as src,\
         open(dst_path, 'wb') as dst:
         dst.write(src.read())

   @property
   def default_filename(self):
      return self._default_filename

   @property
   def url_parts(self):
      return self._url_parts

   @property
   def uid(self):
      return re.search(r'\w+$', self._url_parts.query)[0]

def main():
   parser = argparse.ArgumentParser(
      description="parse through URLs and download the content")
   parser.add_argument('URL_FILE',
      help='file containing a list of URLs. If the file contains ' +
         'other things, this tool extracts those tokens that have ' +
         '"http" in them')
   parser.add_argument('-d', '--dst', default='.',
      help='destination folder to store downloads')
   parser.add_argument('-t', '--tail',
      help='UID of where to start downloading photos. The UID is the ' +
         'identifier at the end of the URL at the query part. For example, in ' +
         'https://scontent-atl3-1.xx.fbcdn.net/v/t34.0-12/' +
         '28313230_10215999386641579_1936966559_n.jpg' +
         '?oh=13b2d5a06c227a937a97229a0a61eaeb&oe=5A937038, the UID here is ' +
         '5A937038. Downloads all photos by default')
   parser.add_argument('-p', '--print-ids', action='store_true',
      help='just print uids')
   parser.add_argument('-l', '--length', action='store_true',
      help='print the number of urls found')
   args = parser.parse_args()

   with URLFileParser(args.URL_FILE) as urp:
      start_capture = False
      urls = urp.get_urls()

      if args.length:
         print(len(urls))
         exit(0)

      for url in urls:
         dl = Downloadable(url)

         if args.print_ids:
            print(dl.uid)

         elif args.tail is None or \
            args.tail and dl.uid == args.tail:
            start_capture = True

         if start_capture:  
            print("downloading {}...".format(dl.default_filename), end='')
            while True:
               try:
                  dl.download(args.dst)
                  break
               except urllib.error.URLError as err:
                  print(err.reason)
               except ConnectionResetError as err:
                  print(err.strerror)
            print("done!")

if __name__ == '__main__':
   main()
