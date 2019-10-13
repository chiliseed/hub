from setuptools import setup


setup(
    name='tools',
    version='0.1',
    scripts=['main.py'],
    install_requires=[
        'Click',
        'pygments',
    ],
    entry_points='''
        [console_scripts]
        tools=main:cli
    ''',
)
