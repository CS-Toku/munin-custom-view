#
#-*- encoding: utf-8 -*-

import re

from munincustom.utils import MachineTuple
from munincustom.graph import Graph, Series
from munincustom.exceptions import ParseError



class AbsParser(object):

    def __init__(self, f):
        if isinstance(f, file):
            self.content_str = f.read()
        elif isinstance(f, str):
            self.content_str = open(f).read()
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
            conf_data = list(map(lambda x:x.strip(), filter(lambda x: x, re.sub('#.*\n', '\n', self.content_str).split('\n'))))
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
        iter_data = re.finditer('^([\w-]+);([\w-]*):([\w\.]+) +(.+)$', self.content_str, re.MULTILINE)

        param_info = {}
        for data in iter_data:
            try:
                mt = MachineTuple(domain=data.group(1), host=data.group(2))
                cat_name, param_name = data.group(3).rsplit('.', 1)
                param = data.group(4)

                if mt not in param_info:
                    param_info[mt] = {}
                if cat_name not in param_info[mt]:
                    param_info[mt][cat_name] = {}
                
                param_info[mt][cat_name][param_name] = param
            except ValueError:
                continue

        # グラフ情報/系列情報を抜き出す
        graph = {}
        series = {}
        strip_prefix = lambda x: x.lstrip('graph_')
        dict_map = lambda f, dic: dict([(f(i[0]), i[1]) for i in dic.items()])
        for mt, param_dic_per_machine in param_info.items():
            graph[mt] = {}
            series[mt] = {}
            for cat_name, param_dic in param_dic_per_machine.items():
                if 'graph_title' in param_dic:
                    strip_dic = dict_map(strip_prefix, param_dic)
                    graph[mt][cat_name] = Graph(mt.domain, mt.host, cat_name, **strip_dic)
                else:
                    cat_name, series_name = cat_name.rsplit('.', 1)
                    series_obj = Series(series_name, **param_dic)

                    if cat_name in series[mt]:
                        series[mt][cat_name].append(series_obj)
                    else:
                        series[mt][cat_name] = [series_obj]

        for mt, v in series.items():
            for cat_name, series_list in v.items():
                for s in series_list:
                    graph[mt][cat_name].add_series(s)

        return graph









