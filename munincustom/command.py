#!/bin/env python
#-*- encoding: utf-8 -*-

from __future__ import print_function

import os
import os.path
import click
import imp
import yaml
from string import Template
from jinja2 import Environment, FileSystemLoader

from munincustom import utils, State
from munincustom.utils.config import ConfigReader
from munincustom.utils.parser import MuninConfigParser, MuninDataParser

from  munincustom.exceptions import FileNotFoundError

def valid_data(checker, *paths):
    return reduce(lambda acc,x: acc and checker(x), paths, True)

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
@click.option('--dest', help='destination file path.')
@click.option('--tmpl', help='template file path.')
@click.option('--part', help='partial template file path.')
@click.option('--folder', help='folder name for munin custom url.')
@click.option('--name', help='name for custom munin page')
def template(conf, mconf, dest, tmpl, folder, part, name):

    chk_not_none = lambda x: x is not None

    config = ConfigReader(conf)

    if mconf is None:
        mconf = config.get('mc', 'munin_conf')

    if tmpl is None:
        tmpl = config.get('template_opt', 'template_file')

    if folder is None:
        folder = config.get('template_opt', 'folder_name')

    if part is None:
        part = config.get('template_opt', 'partial_file')

    if name is None:
        name = config.get('template_opt', 'page_name')

    if not valid_data(check_path, mconf, tmpl, part):
        raise FileNotFoundError(';'.join([str(mconf), str(tmpl), str(part)]))

    _, munin_options = MuninConfigParser(mconf).parse()
    default_dest_path = munin_options['tmpldir'] if 'tmpldir' in munin_options else None
    if dest is None:
        dest = config.get('template_opt', 'dest_file', default_dest_path)

    if not valid_data(chk_not_none, folder, name, dest):
        raise ValueError('Data is None')

    partial = Template(open(part).read()).substitute(
                customview_folder=folder,
                customview_name=name
            )
    template_body = Template(open(tmpl).read()).substitute(customview=partial)
    open(dest, 'w').write(template_body)




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

    if not valid_data(check_path, mconf, recipe) or not valid_data(check_dir, plgdir):
        raise FileNotFoundError(mconf)

    machines, options = MuninConfigParser(mconf, dict(config.items('munin_config'))).parse()
    datafile = options['dbdir'] + '/datafile'
    htmldir = options.get('htmldir')
    htmldir = config.get('munin_config', 'htmldir', htmldir)
    content_dist = '/'.join([htmldir, config.get('mc', 'content_folder')])
    graph_info = MuninDataParser(datafile).parse()
    recipe_list = yaml.load(open(recipe))
    plugin_modules = {}
    machine_state_dict = {}

    for recipe_data in recipe_list:
        # 解析＆生成？
        # domainとhostに含まれているマシンを引き出す
        host_list = list(map(utils.split_domainhost, recipe_data['host']))
        target_machine = dict([(mt, v) for mt, v in graph_info.items()
                              if mt.domain in recipe_data['domain']
                              or mt in host_list])

        if isinstance(recipe_data['source'], dict):
            target = {}
            for mt, graphs in target_machine.items():
                target[mt] = {}
                for k, source in recipe_data['source'].items():
                    series_name = source['series']
                    for cat_name, graph in graphs.items():
                        if series_name in graph.get_series():
                            source_data = graph.get_series()[series_name]
                            source_path = source_data.get_rrd_filepath()
                            fullpath = options['dbdir'] + '/' + source_path
                            target[mt][k] = fullpath, source
                            break

        elif isinstance(recipe_data['source'], list):
            target = {}
            for mt, graphs in target_machine.items():
                target[mt] = []
                for source in recipe_data['source']:
                    series_name = source['series']
                    for cat_name, graph in graphs.items():
                        if series_name in graph.get_series():
                            source_data = graph.get_series()[series_name]
                            source_path = source_data.get_rrd_filepath()
                            fullpath = options['dbdir'] + '/' + source_path
                            target[mt].append((fullpath, source))
                            break
        else:
            raise TypeError('Bad recipe.')

        # plugin moduleの読み込み
        if recipe_data['plugin'] in plugin_modules:
            m = plugin_modules[recipe_data['plugin']]
        else:
            imp_info = imp.find_module(recipe_data['plugin'], [plgdir])
            m = imp.load_module(recipe_data['plugin'], *imp_info)
            plugin_modules[recipe_data['plugin']] = m

        # 解析メソッド呼び出し
        analysis_obj = m.Analysis(recipe_data['tag'], target)
        machine_state = analysis_obj.analysis()
        webview = analysis_obj.make_view()

        # マシンごとの解析ページの出力
        for mt, web_content in webview.items():
            output_file = '/'.join([content_dist, mt.domain, mt.host, analysis_obj.tag + '.html'])
            dir_name = os.path.dirname(output_file)
            if not os.path.lexists(dir_name):
                os.makedirs(dir_name)
            open(output_file, mode='w').write(web_content)

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
            # ホストの集計
            if mt not in machine_total:
                machine_total[mt] = {'warning': 0, 'error': 0}
            machine_total[mt]['warning'] += is_warning
            machine_total[mt]['error'] += is_error
            # ドメインの集計
            if mt.domain not in domain_total:
                domain_total[mt.domain] = {'warning': 0, 'error': 0}
            domain_total[mt.domain]['warning'] += is_warning
            domain_total[mt.domain]['error'] += is_error

            # 各マシンのページを作成
            # 要素の構築
            tag_elem = {
                    'is_success': machine_state == State.SUCCESS,
                    'is_warning': bool(is_warning),
                    'is_error': bool(is_error)
                    }
            tag_elem['tag'] = tag
            tag_elem['page_url'] = tag+'.html'
            if mt not in machine_pages:
                machine_pages[mt] = {}
            machine_pages[mt][tag] = tag_elem

    # 各ドメインのページを作成
    # 要素の構築
    domain_pages = {}
    for mt, state_count in machine_total.items():
        machine_elem = {'state_cnt': state_count}
        machine_elem['tag'] = mt.host
        machine_elem['page_url'] = '/'.join([mt.host, 'index.html'])
        if mt.domain not in domain_pages:
            domain_pages[mt.domain] = {}
        domain_pages[mt.domain][mt.host] = machine_elem

    # ドメインのまとめページを作成
    # 要素の構築
    top_page = {}
    for domain, state_count in domain_total.items():
        domain_elem = {'state_cnt': state_count}
        domain_elem['tag'] = domain
        domain_elem['page_url'] = '/'.join([domain, 'index.html'])
        top_page[domain] = domain_elem

    # 各ページの作成
    # 各マシン
    template_folder_path = config.get('template_opt', 'template_folder')
    env = Environment(loader=FileSystemLoader(template_folder_path, encoding='utf8'))
    tpl = env.get_template('group-list.tmpl')
    for mt, contents in machine_pages.items():
        output_file = '/'.join([content_dist, mt.domain, mt.host, 'index.html'])
        for tag, elem in contents.items():
            continue
        html = tpl.render({}).encode('utf-8')
        open(output_file, 'w').write(html)

    for domain, contents in domain_pages.items():
        output_file = '/'.join([content_dist, domain, 'index.html'])
        for tag, elem in contents.items():
            continue
        html = tpl.render({}).encode('utf-8')
        open(output_file, 'w').write(html)

    output_file = '/'.join([content_dist, 'index.html'])
    for tag, elem in contents.items():
        continue
    html = tpl.render({}).encode('utf-8')
    open(output_file, 'w').write(html)







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

