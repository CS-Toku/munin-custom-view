#!/bin/env python
#-*- encoding: utf-8 -*-

from __future__ import print_function

import os
import os.path
import shutil
import json
import click
import imp
import yaml
from jinja2 import Environment, FileSystemLoader

from munincustom import utils, State
from munincustom.utils.config import ConfigReader
from munincustom.utils.parser import MuninConfigParser, MuninDataParser

from munincustom.exceptions import FileNotFoundError


def valid_data(checker, *paths):
    return reduce(lambda acc, x: acc and checker(x), paths, True)


def check_path(path):
    return bool(isinstance(path, str) and os.path.isfile(path))


def check_dir(path):
    return bool(isinstance(path, str) and os.path.isdir(path))


@click.group()
def cmd():
    pass


@cmd.group()
def make():
    pass


@cmd.group()
def load():
    pass


@cmd.group()
def test():
    pass


@make.command()
@click.option('--conf', help='mc configuration file path.')
@click.option('--mconf', help='munin configuration file path.')
@click.option('--dest', help='destination folder path.')
def template(conf, mconf, dest):

    chk_not_none = lambda x: x is not None

    config = ConfigReader(conf)

    if mconf is None:
        mconf = config.get('mc', 'munin_conf')

    folder = config.get('mc', 'content_folder')
    name = config.get('template_opt', 'page_name')

    if not valid_data(check_path, mconf):
        raise FileNotFoundError(mconf)

    template_folder_path = config.get('template_opt', 'template_folder')
    env = Environment(loader=FileSystemLoader(template_folder_path,
                      encoding='utf8'))
    _, munin_options = MuninConfigParser(mconf).parse()
    tmpldir = munin_options.get('tmpldir')
    default_dest = tmpldir.rstrip('/') if tmpldir is not None else None
    if dest is None:
        dest = config.get('template_opt', 'dest_folder', default_dest)

    if not valid_data(chk_not_none, folder, name, dest):
        raise ValueError('Data is None')

    overview_dest = dest + '/munin-overview.tmpl'
    partial_head_dest = dest + '/partial/head.tmpl'

    tpl = env.get_template('munin-overview.tmpl.tmpl')
    html_template = tpl.render({
        'content_folder': folder.decode('utf-8'),
        'page_name': name.decode('utf-8')
        }).encode('utf-8')
    open(overview_dest, 'w').write(html_template)

    tpl = env.get_template('head.tmpl.tmpl')
    static_folder = config.get('mc', 'static_contents_folder')
    html_template = tpl.render({
        'content_folder': folder.decode('utf-8'),
        'static_contents_folder': static_folder.decode('utf-8')
        }).encode('utf-8')
    open(partial_head_dest, 'w').write(html_template)


@make.command()
@click.option('--conf', help='mc configuration file path.')
@click.option('--mconf', help='munin configuration file path.')
@click.option('--dest', help='destination folder path.')
def static(conf, mconf, dest):

    config = ConfigReader(conf)

    if mconf is None:
        mconf = config.get('mc', 'munin_conf')

    if not valid_data(check_path, mconf):
        raise FileNotFoundError(mconf)

    machines, options = MuninConfigParser(mconf, dict(config.items('munin_config'))).parse()
    htmldir = options.get('htmldir')
    htmldir = config.get('munin_config', 'htmldir', htmldir)
    static_contents_data_path = config.get('mc', 'static_contents_data_path')
    content_folder = config.get('mc', 'content_folder')
    doc_root = '/'.join([htmldir, content_folder])
    static_contents_folder = config.get('mc', 'static_contents_folder')
    static_contents_dest = '/'.join([doc_root, static_contents_folder])

    if not os.path.lexists(doc_root):
        os.makedirs(doc_root)
    if os.path.lexists(static_contents_dest):
        shutil.rmtree(static_contents_dest)
    shutil.copytree(static_contents_data_path, static_contents_dest)

    # JS用static??
    template_folder_path = config.get('template_opt', 'template_folder')
    env = Environment(loader=FileSystemLoader(template_folder_path,
                      encoding='utf8'))
    tpl = env.get_template('customview.js.tmpl')
    js = tpl.render(content_folder=content_folder).encode('utf-8')
    open(static_contents_dest+'/customview.js', 'w').write(js)


@make.command()
@click.option('--conf', help='mc configuration file path.')
@click.option('--mconf', help='munin configuration file path.')
@click.option('--recipe', help='recipe file path.')
@click.option('--plgdir', help='plugin directory.')
@click.option('--dest', help='destination folder path.')
def content(conf, mconf, recipe, plgdir, dest):

    config = ConfigReader(conf)

    if mconf is None:
        mconf = config.get('mc', 'munin_conf')

    if recipe is None:
        recipe = config.get('mc', 'recipe_file')

    if plgdir is None:
        plgdir = config.get('mc', 'plugin_dir')

    if not valid_data(check_path, mconf, recipe) or \
       not valid_data(check_dir, plgdir):
        raise FileNotFoundError(mconf)

    machines, options = MuninConfigParser(mconf, dict(config.items('munin_config'))).parse()
    datafile = options['dbdir'] + '/datafile'
    htmldir = options.get('htmldir')
    htmldir = config.get('munin_config', 'htmldir', htmldir)
    content_folder = config.get('mc', 'content_folder')
    static_contents_folder = config.get('mc', 'static_contents_folder')
    content_dist = '/'.join([htmldir, content_folder])
    page_title = config.get('template_opt', 'page_name')
    graph_info = MuninDataParser(datafile).parse()
    recipe_list = yaml.load(open(recipe))
    template_folder_path = config.get('template_opt', 'template_folder')
    env = Environment(loader=FileSystemLoader(template_folder_path,
                      encoding='utf8'))
    plugin_modules = {}
    machine_state_dict = {}

    tag_list = {}
    for recipe_data in recipe_list:
        # 解析ページ用にドメイン・ホストのリストを作成。
        # レシピに含まれているdomainとhostを全て引き出す
        if not recipe_data.get('is_enable', True) or \
           'host' not in recipe_data and 'domain' not in recipe_data:
            continue
        hosts = list(
                    map(utils.split_domainhost, recipe_data['host'])
                    if 'host' in recipe_data
                    else []
                )
        target_machine = [mt for mt in graph_info
                          if mt in hosts or
                          'domain' in recipe_data and
                          mt.domain in recipe_data['domain']]
        for mt in target_machine:
            if mt.domain not in tag_list:
                tag_list[mt.domain] = {}
            if mt.host not in tag_list[mt.domain]:
                tag_list[mt.domain][mt.host] = []
            tag_list[mt.domain][mt.host].append({
                    'url': recipe_data['tag']+'.html',
                    'name': recipe_data['tag']
                })

    domain_list = [{'url': '../../'+d+'/index.html', 'name': d}
                   for d in tag_list.keys()]
    host_list = dict([(
                        d,
                        [{'url': '../'+h+'/index.html', 'name': h}
                         for h in host_dict]
                    ) for d, host_dict in tag_list.items()])

    tpl = env.get_template('analyzed-page.tmpl')
    for recipe_data in recipe_list:
        # 解析＆生成？
        # domainとhostに含まれているマシンを引き出す
        if not recipe_data.get('is_enable', True) or \
           'host' not in recipe_data and 'domain' not in recipe_data:
            continue
        hosts = list(
                    map(utils.split_domainhost, recipe_data['host'])
                    if 'host' in recipe_data
                    else []
                )
        target_machine = dict([(mt, v) for mt, v in graph_info.items()
                               if mt in hosts or
                               'domain' in recipe_data and
                               mt.domain in recipe_data['domain']])

        all_series = {}
        for mt, graphs in target_machine.items():
            all_series[mt] = {}
            for graph in graphs.values():
                series = graph.get_series()
                all_series[mt].update(series)

        target = {}
        for mt, graphs in target_machine.items():
            target[mt] = {}
            has_series = all_series[mt]
            has_series_name = has_series.keys()
            for k, source in recipe_data['sources'].items():
                recipe_series_list = source['series']
                if not isinstance(recipe_series_list, list):
                    raise TypeError('Series must be  list type.')

                series_list = []
                for series_name in recipe_series_list:
                    if utils.is_glob_pattern(series_name):
                        series_list += utils.glob_match(series_name, has_series_name)
                    elif series_name in has_series_name:
                        series_list.append(series_name)

                series_data = [
                        {
                            'filepath': (options['dbdir'] +
                                         '/' +
                                         has_series[s].get_rrd_filepath()),
                            'series': has_series[s],
                            'source': source
                        }
                        for s in series_list
                    ]
                target[mt][k] = series_data

        # plugin moduleの読み込み
        if recipe_data['plugin'] in plugin_modules:
            m = plugin_modules[recipe_data['plugin']]
        else:
            imp_info = imp.find_module(recipe_data['plugin'], [plgdir])
            m = imp.load_module(recipe_data['plugin'], *imp_info)
            plugin_modules[recipe_data['plugin']] = m

        # 解析メソッド呼び出し
        analysis_kargs = recipe_data.get('args')
        analysis_obj = m.Analysis(recipe_data['tag'], target, analysis_kargs)
        machine_state = analysis_obj.analysis()
        webview = analysis_obj.make_view()

        # マシンごとの解析ページの出力
        param = {
                'title': page_title.decode('utf-8'),
                'domain': None,
                'domains': domain_list,
                'host': None,
                'hosts': None,
                'tag': analysis_obj.tag,
                'tags': None,
                'munin_root_depth': '../'*3,
                'content_folder': content_folder,
                'static_contents_folder': static_contents_folder
                }
        for mt, web_content in webview.items():
            param['domain'] = mt.domain
            param['host'] = mt.host
            param['hosts'] = host_list[mt.domain]
            param['tags'] = tag_list[mt.domain][mt.host]
            param['web_content'] = web_content
            html = tpl.render(param).encode('utf-8')
            output_file = '/'.join([content_dist, mt.domain, mt.host, analysis_obj.tag + '.html'])
            dir_name = os.path.dirname(output_file)
            if not os.path.lexists(dir_name):
                os.makedirs(dir_name)
            open(output_file, mode='w').write(html)

        # マシンの状態を格納
        tag = recipe_data['tag']
        for mt, state in machine_state.items():
            if mt not in machine_state_dict:
                machine_state_dict[mt] = {}
            machine_state_dict[mt][tag] = state

    domain_total = {}
    machine_total = {}
    machine_pages = {}
    for mt, states in machine_state_dict.items():
        # host名がない場合は無視。
        if mt.host is None:
            continue
        for tag, state in states.items():
            is_error = 1 if state == State.ERROR else 0
            is_warning = 1 if state == State.WARNING else 0
            is_info = 1 if state == State.INFO else 0
            # ホストの集計
            if mt not in machine_total:
                machine_total[mt] = {'warning': 0, 'error': 0, 'info': 0}
            machine_total[mt]['warning'] += is_warning
            machine_total[mt]['error'] += is_error
            machine_total[mt]['info'] += is_info
            # ドメインの集計
            if mt.domain not in domain_total:
                domain_total[mt.domain] = {'warning': 0, 'error': 0, 'info': 0}
            domain_total[mt.domain]['warning'] += is_warning
            domain_total[mt.domain]['error'] += is_error
            domain_total[mt.domain]['info'] += is_info

            # 各マシンのページを作成
            # 要素の構築
            tag_elem = {
                    'is_success': state == State.SUCCESS,
                    'is_warning': bool(is_warning),
                    'is_error': bool(is_error),
                    'is_info': bool(is_info)
                    }
            tag_elem['name'] = tag
            tag_elem['url'] = tag+'.html'
            if mt not in machine_pages:
                machine_pages[mt] = {}
            machine_pages[mt][tag] = tag_elem

    # 各ドメインのページを作成
    # 要素の構築
    domain_pages = {}
    for mt, state_count in machine_total.items():
        machine_elem = {'state_cnt': state_count}
        machine_elem['name'] = mt.host
        machine_elem['url'] = '/'.join([mt.host, 'index.html'])
        if mt.domain not in domain_pages:
            domain_pages[mt.domain] = {}
        domain_pages[mt.domain][mt.host] = machine_elem

    # ドメインのまとめページを作成
    # 要素の構築
    top_page = {}
    for domain, state_count in domain_total.items():
        domain_elem = {'state_cnt': state_count}
        domain_elem['name'] = domain
        domain_elem['url'] = '/'.join([domain, 'index.html'])
        top_page[domain] = domain_elem

    # 各ページの作成
    # 各マシン
    tpl = env.get_template('item-list-nobadge.tmpl')
    param = {
            'title': page_title.decode('utf-8'),
            'domain': None,
            'domains': None,
            'host': None,
            'hosts': None,
            'tags': None,
            'item_list': None,
            'munin_root_depth': '../'*3,
            'content_folder': content_folder,
            'static_contents_folder': static_contents_folder
            }
    param['domains'] = [{'url': '../../'+d+'/index.html', 'name': d}
                        for d in domain_pages]
    hosts_dict = dict([(
                        d,
                        [{'url': '../'+h+'/index.html', 'name': h}
                         for h in host_dict]
                    ) for d, host_dict in domain_pages.items()])
    for mt, contents in machine_pages.items():
        param['domain'] = mt.domain
        param['host'] = mt.host
        param['hosts'] = hosts_dict[mt.domain]
        param['tags'] = contents.values()
        param['item_list'] = contents.values()
        output_file = '/'.join([content_dist, mt.domain, mt.host, 'index.html'])
        html = tpl.render(param).encode('utf-8')
        open(output_file, 'w').write(html)

    # 各ドメイン
    tpl = env.get_template('item-list-badge.tmpl')
    param = {
            'title': page_title.decode('utf-8'),
            'domain': None,
            'domains': None,
            'hosts': None,
            'item_list': None,
            'munin_root_depth': '../'*2,
            'content_folder': content_folder,
            'static_contents_folder': static_contents_folder
            }
    param['domains'] = [{'url': '../'+d+'/index.html', 'name': d}
                        for d in domain_pages]
    hosts_dict = dict([(
                        d,
                        [{'url': h+'/index.html', 'name': h}
                         for h in host_dict]
                    ) for d, host_dict in domain_pages.items()])
    for domain, contents in domain_pages.items():
        param['domain'] = domain
        param['hosts'] = hosts_dict[domain]
        param['item_list'] = contents.values()
        output_file = '/'.join([content_dist, domain, 'index.html'])
        for tag, elem in contents.items():
            continue
        html = tpl.render(param).encode('utf-8')
        open(output_file, 'w').write(html)

    # トップ
    param = {
            'title': page_title.decode('utf-8'),
            'domains': [{'url': d+'/index.html', 'name': d}
                        for d in domain_pages],
            'item_list': None,
            'munin_root_depth': '../'*1,
            'content_folder': content_folder,
            'static_contents_folder': static_contents_folder
            }
    output_file = '/'.join([content_dist, 'index.html'])
    param['item_list'] = top_page.values()
    html = tpl.render(param).encode('utf-8')
    open(output_file, 'w').write(html)

    # Munin Topページのラベル用のJSONを生成
    mt_state_dict = {}
    for mt, state_count in machine_total.items():
        k = mt.domain + ';' + mt.host
        if state_count['error'] > 0:
            mt_state_dict[k] = State.ERROR
        elif state_count['warning'] > 0:
            mt_state_dict[k] = State.WARNING
        elif state_count['info'] > 0:
            mt_state_dict[k] = State.INFO
        else:
            mt_state_dict[k] = State.SUCCESS

    output_file = '/'.join([content_dist, 'machine-state.json'])
    json.dump(mt_state_dict, open(output_file, 'w'))


@test.command()
@click.option('--conf', help='mc configuration file path.')
@click.option('--mconf', help='munin configuration file path.')
@click.option('--recipe', help='recipe file path.')
@click.option('--plgdir', help='plugin directory.')
def recipe(conf, mconf, recipe, plgdir):
    print('Prepare...\n')

    try:
        config = ConfigReader(conf)
    except FileNotFoundError:
        print('mc configuration file not found: ' + conf)
        return

    if mconf is None:
        mconf = config.get('mc', 'munin_conf')
    if not valid_data(check_path, mconf):
        print('munin configuration file not found: ' + mconf)
        return

    if recipe is None:
        recipe = config.get('mc', 'recipe_file')
    if not valid_data(check_path, recipe):
        print('recipe file not found: ' + recipe)
        return

    if plgdir is None:
        plgdir = config.get('mc', 'plugin_dir')
    if not valid_data(check_dir, plgdir):
        print('plugin directory not found: ' + plgdir)
        return

    try:
        machines, options = MuninConfigParser(mconf, dict(config.items('munin_config'))).parse()
    except Exception:
        print('Munin configuration file parse failed.')

    datafile = options['dbdir'] + '/datafile'
    try:
        graph_info = MuninDataParser(datafile).parse()
    except Exception:
        print('Munin datafile parse failed.')

    try:
        recipe_list = yaml.load(open(recipe))
    except Exception:
        print('Recipe parse failed.')

    exist_plugin_list = []

    for recipe_data in recipe_list:
        # Tagの確認
        if not 'tag' in recipe_data:
            i = recipe_list.index(recipe_data)
            print('Error: tag is not specified({0})'.format(i))
            return
        print('check tag: {0} => '.format(recipe_data['tag']), end='')

        # Pluginの確認
        if not 'plugin' in recipe_data:
            print('Error: plugin is not specified({0})'.format(i))
            return
        if not recipe_data['plugin'] in exist_plugin_list:
            try:
                imp_info = imp.find_module(recipe_data['plugin'], [plgdir])
                imp.load_module(recipe_data['plugin'], *imp_info)
            except Exception:
                print('Error: plugin load failed({0})'.format(recipe_data['plugin']))
                return
            exist_plugin_list.append(recipe_data['plugin'])

        # domain, hostの確認
        if 'domain' not in recipe_data and 'host' not in recipe_data:
            print('Error: machine is not specified by domain or host({0})'.format(i))
            return

        # domainの確認
        if 'domain' in recipe_data:
            if not isinstance(recipe_data['domain'], list) and recipe_data['domain']:
                print('Error: domain struct is not list type')
                return
            domain_data_set = set([mt.domain for mt in graph_info.keys()])
            domain_recipe_set = set(recipe_data['domain'])
            if not domain_recipe_set <= domain_data_set:
                print('Error: The specified domain is not in munin datafile({0})'.format(
                        list(domain_recipe_set-domain_data_set)
                    ))
                return

        # hostの確認
        if 'host' in recipe_data:
            if not isinstance(recipe_data['host'], list) and recipe_data['host']:
                print('Error: host struct is not list type')
                return
            host_data_set = set(graph_info.keys())
            host_recipe_set = set([utils.split_domainhost(host) for host in recipe_data['host']])
            if not host_recipe_set <= host_data_set:
                print('Error: The specified host is not in munin datafile({0})'.format(
                        list(host_recipe_set-host_data_set)
                    ))
                return

        # seriesの確認
        if not 'source' in recipe_data:
            pass

        try:
            if isinstance(recipe_data['source'], list):
                recipe_series = set([x['series'] for x in recipe_data['source']])
            elif isinstance(recipe_data['source'], dict):
                recipe_series = set([x['series'] for x in recipe_data['source'].values()])
            else:
                raise TypeError()
        except KeyError:
            print('Error: series is not specified')
            return
        except TypeError:
            print('Error: source value is not list or dict')
            return
        except Exception:
            print('Error: Unexpected error')
            return

        target_machines = [mt for mt in graph_info.keys() if mt.domain in recipe_data['domain']]
        target_machines += [utils.split_domainhost(host) for host in recipe_data['host']]


        for mt in target_machines:
            nest = [set(graph.get_series().keys()) for graph in graph_info[mt].values()]
            machine_series = set()
            for s in nest:
                machine_series |= s
            if not recipe_series <= machine_series:
                print("{0};{1} doesn't have these series {2}".format(
                        mt.domain,
                        mt.host,
                        list(recipe_series-machine_series)
                    ))
                return

        print('OK.')

    print('\nRecipe test was successful.\n')




@test.command()
@click.option('--conf', help='mc configuration file path.')
@click.option('--plgdir', help='plugin directory.')
@click.argument('plugin')
def load_plugin(conf, plgdir, plugin):
    if plgdir is None:
        try:
            config = ConfigReader(conf)
        except FileNotFoundError:
            print('mc configuration file not found: ' + conf)
            return
        plgdir = config.get('mc', 'plugin_dir')

    if not valid_data(check_dir, plgdir):
        print('plugin directory not found')
        return

    try:
        imp_info = imp.find_module(plugin, [plgdir])
        m = imp.load_module(plugin, *imp_info)
    except Exception:
        print('Module import error')
        return

    if hasattr(m, 'Analysis') and hasattr(m.Analysis, 'analysis') and hasattr(m.Analysis, 'make_view'):
        print('\nplugin load test was successful.\n')
    else:
        print('There is not implemented method or class in this module.')


def main():
    cmd()


if __name__ == '__main__':
    main()

