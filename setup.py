from setuptools import setup, find_packages

setup(
    name='munincustom',
    version='0.0.1',
    description='Munin Cuntom Viewer',
    author='CS_Toku',
    author_email='cs_toku@sce-toku.jp',
    packages=find_packages(),
    package_data={
        'munincustom': [
            'templates/*.tmpl',
            '_static/*',
            'utils/config/default.conf',
        ]
    },
    data_files=[
        ('/etc/munin/customview', ['munin-custom.conf', 'recipe.yaml']),
        ('/etc/munin/customview/plugins/list_series',
            ['plugins/list_series/__init__.py',
             'plugins/list_series/body.tmpl',
             'plugins/list_series/option.yaml'])
    ],
    entry_points={'console_scripts': [
        'mc = munincustom.command:main',
    ]},
    install_requires=[
        'PyRRD',
        'click',
        'Jinja2',
        'PyYAML'
    ],
    extras_require={
        'test': ['pytest']
    },
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: System :: Monitoring',
    ]
)
