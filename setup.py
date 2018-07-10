from setuptools import setup

setup(
    name='conversion-server',
    packages=['conversion-server'],
    include_package_data=True,
    install_requires=[
        'flask',
        'babelfish',
        'qtfaststart',
        'transitions',
        'tmdbsimple',
        'mutagen',
        'configobj',
        'tvdb-api',
        'waitress'
    ]
)
