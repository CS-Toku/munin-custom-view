from setuptools import setup, find_packages

setup(
    name='munincustom',
    version='0.0.0',
    description='Munin Cuntom Viewer',
    author='Takuya Tokuda',
    author_email='tokuda_takuya@griphone.co.jp',
    packages=find_packages(),
    package_data={
        'munincustom': [
            'templates/*.tmpl',
            'utils/config/default.conf',
        ]
    },
    data_files=[
        ('/etc/munin', ['munin-custom.conf']),
    ],
    entry_points={'console_scripts': [
        'mc = munincustom.command:main',
    ]},
    install_requires={
        'click': ['click'],
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
