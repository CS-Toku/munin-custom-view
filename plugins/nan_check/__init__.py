#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import math
import datetime

from jinja2 import Environment, FileSystemLoader

from munincustom.plugin import BaseAnalysisClass
from munincustom import State


class Analysis(BaseAnalysisClass):

    def check_nan_period(self, seq):
        series_nan_periods = {}
        for series_data in seq:
            in_nan_period = False
            nan_periods = []
            for t in series_data['data']:
                if not in_nan_period and math.isnan(t[1]):
                    start = datetime.datetime.fromtimestamp(t[0])
                    in_nan_period = True
                elif in_nan_period and not math.isnan(t[1]):
                    end = datetime.datetime.fromtimestamp(t[0])
                    in_nan_period = False
                    nan_periods.append({'start': start, 'end': end})

            if in_nan_period:
                end = datetime.datetime.fromtimestamp(t[0])
                nan_periods.append({'start': start.isoformat()+' UTC', 'end': end.isoformat()+' UTC'})

            series_name = str(series_data['series'])
            series_nan_periods[series_name] = nan_periods, series_data['series'].get_link()

        return series_nan_periods

    def is_nan_last(self, seq):
        last_nan = {}
        for series_data in seq:
            last_data = reduce(lambda acc, x: acc if acc[0] > x[0] else x,
                               series_data['data'],
                               [0, 0])

            series_name = str(series_data['series'])
            last_nan[series_name] = math.isnan(last_data[1])

        return last_nan

    def analysis(self):
        mt_state_dict = {}
        analysis_mt_dict = {}
        for mt, sources in self.rrd_data.items():
            mt_state_dict[mt] = State.SUCCESS
            series_nan_periods = self.check_nan_period(sources['period'])
            last_nan = self.is_nan_last(sources['period'])

            analysis_data = []
            for series_name, (nan_periods, link) in series_nan_periods.items():
                analysis_info = {
                                'name': series_name,
                                'nan_periods': nan_periods,
                                'link': self.munin_root_path + link
                            }

                # 最新のデータがNaNだったらError
                if last_nan[series_name]:
                    mt_state_dict[mt] = State.get_high_priority_state(
                                            mt_state_dict[mt],
                                            State.ERROR)
                    analysis_info['state'] = State.ERROR
                    analysis_info['detail'] = 'Last data is NaN'

                # 期間中にNaNがあったらWarning
                elif len(nan_periods) > 0:
                    mt_state_dict[mt] = State.get_high_priority_state(
                                            mt_state_dict[mt],
                                            State.WARNING)
                    analysis_info['state'] = State.WARNING
                    analysis_info['detail'] = 'Found NaN data in period'

                # NaNがなかった場合
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
                     for mt, data in self.analyzed_data.items()])

