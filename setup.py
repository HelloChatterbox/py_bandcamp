from distutils.core import setup

setup(
    name='py_bandcamp',
    version='0.4.2',
    packages=['py_bandcamp'],
    install_requires=["bs4", "lxml"],
    url='https://github.com/JarbasAl/py_bandcamp',
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='bandcamp data scrapper'
)
