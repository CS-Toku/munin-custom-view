#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import math

from jinja2 import Environment, FileSystemLoader

from munincustom.plugin import BaseAnalysisClass
from munincustom import State


class Analysis(BaseAnalysisClass):

    def get_max_values_with_link(self, seq):
        max_values = {}
        for series_data in seq:
            try:
                max_value = max([x[1] for x in series_data['data']
                                 if not math.isnan(x[1])])
            except ValueError:
                max_value = None

            series_name = str(series_data['series'])
            max_values[series_name] = max_value, series_data['series'].get_link()

        return max_values

    def analysis(self):
        mt_state_dict = {}
        analysis_mt_dict = {}
        for mt, sources in self.rrd_data.items():
            mt_state_dict[mt] = State.SUCCESS
            max_new_data = self.get_max_values_with_link(sources['new_data'])
            max_period_data = self.get_max_values_with_link(sources['period'])

            analysis_data = []
            for series_name, (max_value, link) in max_new_data.items():
                analysis_info = {
                                'name': series_name,
                                'new_data': max_value,
                                'period': max_period_data.get(series_name)[0],
                                'link': self.munin_root_path + link
                            }
                # new_dataに対応する期間データの系列名がないとき
                if series_name not in max_period_data:
                    mt_state_dict[mt] = State.INFO
                    analysis_info['state'] = State.INFO
                    analysis_info['detail'] = 'Not found the corresponding series'

                # new_data, periodの全期間に対して有効なデータがなかった場合
                elif max_value is None or max_period_data[series_name] is None:
                    mt_state_dict[mt] = State.ERROR
                    analysis_info['state'] = State.ERROR
                    analysis_info['detail'] = 'Not found the corresponding series'

                # new_dataの値が大きかった場合
                elif max_value > max_period_data[series_name]:
                    mt_state_dict[mt] = State.get_high_priority_state(
                                            mt_state_dict[mt],
                                            State.WARNING)
                    analysis_info['state'] = State.WARNING
                    analysis_info['detail'] = 'UPDATE max value'

                # 期間中のデータより値が小さかった場合
                else:
                    mt_state_dict[mt] = State.get_high_priority_state(
                                            mt_state_dict[mt],
                                            State.SUCCESS)
                    analysis_info['state'] = State.SUCCESS
                    analysis_info['detail'] = ''

                analysis_data.append(analysis_info)

            analysis_mt_dict[mt] = analysis_data

        self.analyzed_data = analysis_mt_dict
        return mt_state_dict

    def make_view(self):
        state = State.get_state_dict()
        env = Environment(loader=FileSystemLoader(self.rootdir,
                        encoding='utf8'))
        tpl = env.get_template('body.tmpl')
        return dict([(mt, tpl.render(analyzed_data=data, state=state))
                     for mt,data in self.analyzed_data.items()])

