from distutils.core import setup

setup(
    name='jeeves',
    version='0.1dev',
    #todo(chem): need to suffle everything in lib and bin directories.
    packages=[],
    scripts=[
        'jeeves.py', 'sendtoconfluence.py',
        'report.py', 'functions.py',
    ],
    data_files=[
        ('templates', ['templates/macros.html',
                       'templates/remind_template.html',
                       'templates/report_template.html'])
    ],
    license='docs/LICENSE',
    long_description=open('docs/README.md').read(),
    install_requires=[
        'python-jenkins',
        'pyyaml==5.3.1',
        'jinja2==2.10.3',
        'python-bugzilla==2.3.0',
        'jira==2.0.0',
    ])
