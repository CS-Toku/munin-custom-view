#
#-*- encoding: utf-8 -*-

import re

class ParseError(Exception):
    pass

class MuninConfigParser:
    def __init__(self, conf):
        if isinstance(conf, file):
            self.conf_str = conf.read()
        elif isinstance(conf, str):
            self.conf_str = open(conf).read()
        else:
            raise TypeError()

        self.options = None
        self.machines = None
        try:
            self.parse()
        except Exception:
            raise ParseError()

    def parse(self):
        # コメント部分を除去=>改行で分割=>空文字をリストから除去=>各要素にstrip
        conf_data = list(map(lambda x:x.strip(), filter(lambda x: x, re.sub('#.*\n', '\n', self.conf_str).split('\n'))))
        if conf_data:
            domain_host = None
            machine_option = {None:{}}
            for c in conf_data:
                res = re.search('\[(\w+)(;)?(\w+)?\]', c)
                if res is not None:
                    d, s, m = res.groups()
                    domain_host = (d, m) if s is not None else (d, d)
                    machine_option[domain_host] = {}
                else:
                    k, v = c.split(' ', 1)
                    machine_option[domain_host][k] = v

            self.options = machine_option.pop(None)
            self.machines = machine_option


