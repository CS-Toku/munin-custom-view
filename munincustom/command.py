#!/bin/env python
#-*- encoding: utf-8 -*-

import os
import os.path
import click
import imp
import yaml
from string import Template

from munincustom import utils
from munincustom.utils.config import ConfigReader
from munincustom.utils.parser import MuninConfigParser, MuninDataParser

from  munincustom.exceptions import FileNotFoundError

def valid_data(checker, *paths):
    return reduce(lambda acc,x: acc and checker(x), paths, True)

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

    chk_path = lambda path: bool(isinstance(path, str) and os.path.isfile(path))
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

    if not valid_data(chk_path, mconf, tmpl, part):
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
def content(conf, mconf, recipe, dest):
    chk_path = lambda path: bool(isinstance(path, str) and os.path.isfile(path))

    config = ConfigReader(conf)

    if mconf is None:
        mconf = config.get('mc', 'munin_conf')

    if recipe is None:
        recipe = config.get('mc', 'recipe_file')


    if not valid_data(chk_path, mconf, recipe):
        raise FileNotFoundError(mconf)

    machines, options = MuninConfigParser(mconf, dict(config.items('munin_config'))).parse()
    datafile = options['dbdir'] + '/datafile'
    graph_info = MuninDataParser(datafile).parse()
    recipe_list = yaml.load(open(recipe))
    plugin_dir = config.get('mc', 'plugin_dir')
    plugin_modules = {}

    for recipe_data in recipe_list:
    # 解析＆生成？
        #domainとhostに含まれているマシンを引き出す
        host_list = list(map(utils.split_domainhost, recipe_data['host']))
        target_machine = dict([(mt, v) for mt, v in graph_info.items()
                            if mt.domain in recipe_data['domain']
                            or mt in host_list ])

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

        if recipe_data['plugin'] in plugin_modules:
            m = plugin_modules[recipe_data['plugin']]
        else:
            imp_info = imp.find_module(recipe_data['plugin'], [plugin_dir])
            m = imp.load_module(recipe_data['plugin'], *imp_info)
            plugin_modules[recipe_data['plugin']] = m

        analysis_obj = m.Analysis(recipe_data['tag'], target)
        machine_state = analysis_obj.analysis()
        webview = analysis_obj.make_view()

        content_dist = config.get('mc', 'content_dist', options['htmldir'])
        for mt, web_content in webview.items():
            output_file = '/'.join([content_dist, mt.domain, mt.host, analysis_obj.tag + '.html'])
            dir_name = os.path.dirname(output_file)
            if not os.path.lexists(dir_name):
                os.makedirs(dir_name)
            open(output_file, mode='w').write(web_content)




@test.command()
@click.option('--conf', help='mc configuration file path.')
@click.option('--mconf', help='munin configuration file path.')
@click.option('--recipe', help='recipe file path.')
@click.option('--plgdir', help='plugin directory.')
def recipe(conf, mconf, recipe, plgdir):
    pass


@test.command()
@click.option('--conf', help='mc configuration file path.')
@click.option('--plgdir', help='plugin directory.')
@click.argument('plugin', help='mc configuration file path.')
def plugin(conf, plgdir, plugin):
    pass





def main():
    cmd()


if __name__ == '__main__':
    main()

