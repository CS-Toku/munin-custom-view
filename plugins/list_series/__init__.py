#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from jinja2 import Environment, FileSystemLoader

from munincustom.plugin import BaseAnalysisClass
from munincustom import State


class Analysis(BaseAnalysisClass):

    def analysis(self):
        mt_state_dict = {}
        analysis_mt_dict = {}
        for mt, sources in self.rrd_data.items():
            mt_state_dict[mt] = State.SUCCESS
            series_names = [(str(s['series']), self.munin_root_path + s['series'].get_link())
                            for s in sources['series']]
            series_names.sort()
            analysis_mt_dict[mt] = series_names

        self.analyzed_data = analysis_mt_dict
        return mt_state_dict

    def make_view(self):
        env = Environment(loader=FileSystemLoader(self.rootdir,
                        encoding='utf8'))
        tpl = env.get_template('body.tmpl')
        return dict([(mt, tpl.render(analyzed_data=data))
                     for mt,data in self.analyzed_data.items()])

