#!/usr/bin/env python
# encoding: utf-8

import requests
from BeautifulSoup import BeautifulSoup
import re


class ContentExtractor(object):
    def __init__(self, url='', html='', threshold=173):
        self.url = url
        self.threshold = threshold
        self.plain_text = ''
        self.html_text = ''
        self.html = html
        self.content = ''
        self.blocks = []
        self.lines = ()
        self.len_per_lines = []
        self.title = ''

    def _pre_process(self):
        if self.html == '':
            response = requests.get(self.url)
            self.html = response.text
        css_soup = BeautifulSoup(self.html)
        if css_soup.find('h1') is not None:
            self.title = css_soup.find('h1').text
        elif css_soup.find('title') is not None:
            self.title = css_soup.find('title').text
        else:
            return
        plain_text, html_text = self._clean_html(self.html)
        self.plain_text = plain_text
        self.html_text = html_text

    def _extract(self, threshold=173):
        if self.plain_text is '':
            return
        self.lines = tuple(self.plain_text.split('\n'))
        for i in range(len(self.lines)):
            length = len(re.sub(r'\s*', '', self.lines[i]))
            self.len_per_lines.append(length)
        self._caculate_block(3)
        start = 0
        end = 0
        while True:
            start = self._find_surge(end, threshold)
            if start < 0:
                break
            end = self._find_dive(start)
            self.content += '\n'.join(self.lines[start:end])
        self.content = re.sub(r'\n', '[crlf]', self.content)
        self.content = re.sub(r'\s*', '', self.content)
        self.content = re.sub(r'(?:\[crlf\])+', '\n', self.content)
        if len(self.content) == 0:
            self.title = ''

    def _find_surge(self, start, threshold):
        for i in range(start, len(self.blocks) - 2):
            if self.blocks[i] > threshold\
                and self.blocks[i+1] > threshold\
                and self.blocks[i+2] > threshold:
                return i
        return -1

    def _find_dive(self, surge):
        for i in range(surge+1, len(self.blocks)-1):
            if self.blocks[i] == 0 and self.blocks[i+1] == 0:
                return i
        return len(self.blocks) - 1

    def _caculate_block(self, blockWidth):
        self.blocks[:] = []
        for i in range(len(self.len_per_lines) - blockWidth + 1):
            sumLen = sum(self.len_per_lines[i+j] for j in range(blockWidth))
            self.blocks.append(sumLen)

    def _clean_html(self, html):
        regex = re.compile(
            r'(?:<!DOCTYPE.*?>)|'  #doctype
            r'(?:<head[\S\s]*?>[\S\s]*?</head>)|'
            r'(?:<!--[\S\s]*?-->)|'  #comment
            r'(?:<script[\S\s]*?>[\S\s]*?</script>)|'  # js...
            r'(?:<style[\S\s]*?>[\S\s]*?</style>)', re.IGNORECASE)  # css

        html_text = regex.sub('', html)
        html_text = re.sub(r"</p>|<br.*?/>", '[crlf]', html_text)
        plain_text = re.sub(r"<[\s\S]*?>", '', html_text)
        return plain_text, html_text

    def execute(self):
        self._pre_process()
        self._extract()

if __name__ == '__main__':
    # ce = ContentExtractor('http://www.csdn.net/article/2015-02-26/2824020')
    ce = ContentExtractor('http://beiyuu.com/religion-basic/')
    # ce = ContentExtractor('http://beiyuu.com')
    ce.execute()
    print ce.title
    print ce.content
