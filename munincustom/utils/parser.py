#
#-*- encoding: utf-8 -*-

import re
from collections import namedtuple

from munincustom.exceptions import ParseError


MachineTuple = namedtuple('MachineTuple', ['domain', 'host'])

class AbsParser(object):

    def __init__(self, conf):
        if isinstance(conf, file):
            self.conf_str = conf.read()
        elif isinstance(conf, str):
            self.conf_str = open(conf).read()
        else:
            raise TypeError()

    def parse(self):
        pass

class MuninConfigParser(AbsParser):

    def __init__(self, conf, default_options={}):
        super(MuninConfigParser, self).__init__(conf)
        self.__default_options = default_options

    def parse(self, load_default=True):
        try:
            # コメント部分を除去=>改行で分割=>空文字をリストから除去=>各要素にstrip
            conf_data = list(map(lambda x:x.strip(), filter(lambda x: x, re.sub('#.*\n', '\n', self.conf_str).split('\n'))))
            if conf_data:
                domain_host = None
                machine_option = {None:self.__default_options}
                for c in conf_data:
                    res = re.search('\[(\w+)(;)?(\w+)?\]', c)
                    if res is not None:
                        d, s, m = res.groups()
                        domain_host = MachineTuple(d, m) if s is not None else MachineTuple(d, d)
                        machine_option[domain_host] = {}
                    else:
                        # ここでincludeがあった場合は読み込む必要あり（未実装）
                        k, v = c.split(' ', 1)
                        machine_option[domain_host][k] = v

                options = machine_option.pop(None)
                machines = machine_option

            else:
                raise ParseError('No data?')

        except ParseError as e:
            raise e
        except Exception:
            raise ParseError()

        return machines, options


class MuninDataParser(AbsParser):

    def parse(self):
        return self.conf_str







