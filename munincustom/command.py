#!/bin/env python
#-*- encoding: utf-8 -*-

import os
import click
from string import Template

import munincustom
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
@click.option('--dest', help='destination folder path.')
def content(conf, mconf, dest):
    pass



@load.command()
@click.option('--conf', help='mc configuration file path.')
@click.option('--mconf', help='munin configuration file path.')
@click.option('--dest', help='destination folder path.')
def graph(conf, mconf, dest):
    chk_path = lambda path: bool(isinstance(path, str) and os.path.isfile(path))

    config = ConfigReader(conf)

    if mconf is None:
        mconf = config.get('mc', 'munin_conf')


    if not valid_data(chk_path, mconf):
        raise FileNotFoundError(mconf)

    machines, options = MuninConfigParser(mconf, dict(config.items('munin_config'))).parse()
    datafile = options['dbdir'] + '/datafile'
    for k in machines:
        print(k)

    for k,v in options.items():
        print(k,v)

    graph_info = MuninDataParser(datafile).parse()

    for g in graph_info[0].values():
        for a in g.values():
            print(a['graph_title'])









def main():
    cmd()


if __name__ == '__main__':
    main()

