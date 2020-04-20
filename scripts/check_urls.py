import requests
import glob
import re


def test_urls(files):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 6.0; Fiona CI check)'}

    for fpath in files:
        print("Processing: {}".format(fpath))
        with open(fpath) as f:

            text = f.read()
            urls = re.findall('(https?:\/\/[^\s`>\'"()]+)', text)

            for url in urls:
                http_code = None
                try:
                    r = requests.get(url, headers=headers)
                    http_code = r.status_code
                    warn = ''
                    if not http_code == 200:
                        warn = ' <--- !!!'
                except Exception as e:
                    warn = str(e)

                if len(warn) > 0:
                    print("\t {url} HTTP code: {http} {warn}".format(url=url,
                                                                     http=http_code,
                                                                     warn=warn)
                          )


print("Test URLs in documentation")
test_urls(glob.glob('**/*.rst', recursive=True))
print('')
print('Test URLs in code')
test_urls(glob.glob('fiona/**/*.py', recursive=True))
