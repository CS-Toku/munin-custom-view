#!/bin/env python
#-*- encoding: utf-8 -*-

import os
import click
from mcp import MuninConfigParser
from string import Template
from ConfigParser import ConfigParser

config_file_path='mc.conf'
template_str = """
<TMPL_IF NAME="NCATEGORIES">
    [<a href="<TMPL_VAR NAME="R_PATH">/{customview_folder}/<TMPL_LOOP NAME="PATH"><TMPL_IF NAME="pathname"><TMPL_VAR ESCAPE="URL" NAME="PATHNAME">/</TMPL_IF></TMPL_LOOP>index.html">{customview_name}</a>]
</TMPL_IF>
"""
default_filepath = {
        'munin_conf': '/etc/munin/munin.conf',
        'dest_file': '/etc/munin/templates/munin-overview.tmpl',
        'htmldir': '/var/www/html/munin',
        'template_file': 'templates/munin-overview.tmpl.tmpl',
        'folder_name': 'custom',
        'page_name': 'CustomPage'
        }

def get_valid_path(*args):
    return reduce(lambda acc, x: acc or validate_filepath(x), args, None)

def get_confdata(conf_file):
    config = ConfigParser()
    config.read(conf_file)
    return config

def take_valid_data(arg, config, sec, opt, default_value=None):
    return arg if arg is not None else config.get(sec, opt) \
               if config.has_option(sec, opt) else default_value \
               if default_value is not None else default_filepath[opt]

def validate_filepath(path):
    return path if os.path.isfile(path) else None


@click.group()
def cmd():
    pass

@cmd.group()
def make():
    pass


@make.command()
@click.option('--conf',  default=config_file_path, help='mc configuration file path.')
@click.option('--mconf', help='munin configuration file path.')
@click.option('--dest', help='destination file path.')
@click.option('--tmpl', help='template file path.')
@click.option('--folder', help='folder name for munin custom url.')
@click.option('--name', help='name for custom munin page')
def template(conf, mconf, dest, tmpl, folder, name):
    if not validate_filepath(conf):
        raise ValueError()
    config = get_confdata(conf)
    mconf = take_valid_data(mconf, config, 'mc',  'munin_conf')
    if not validate_filepath(mconf):
        raise ValueError()

    default_dest_path = mconf_data.options['tmpldir'] if 'tmpldir' in mconf_data.options else None
    mconf_data = MuninConfigParser(mconf)
    dest = take_valid_data(dest, config,  'template_opt', 'dest_file', default_dest_path)
    template_filepath = take_valid_data(tmpl, config,  'template_opt', 'template_file')
    folder_name = take_valid_data(folder, config, 'template_opt', 'folder_name')
    page_name = take_valid_data(name, config, 'template_opt', 'page_name')

    partial = template_str.format(customview_folder=folder_name, customview_name=page_name)
    template_body = Template(open(template_filepath).read()).substitute(customview=partial)
    open(dest, 'w').write(template_body)




@make.command()
@click.option('--conf',  default=config_file_path, help='mc configuration file path.')
@click.option('--mconf', help='munin configuration file path.')
@click.option('--dest', help='destination folder path.')
def content(conf, mconf, dest):
    pass



if __name__ == '__main__':
    cmd()
