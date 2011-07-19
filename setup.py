from setuptools import setup
from bevis import version
version = '.'.join(str(i) for i in version)

long_description = """\
bevis is a syslog endpoint that forwards messages to an AMQP server.
"""
setup(name='bevis',
      version=version,
      description="syslog-to-amqp bridge",
      long_description=long_description,
      author='Brian K. Jones',
      author_email='bkjones@gmail.com',
      url='http://github.com/bkjones/bevis',
      py_modules=['bevis_run'],
      packages=['bevis'],
      requires=['tornado', 'pika', 'loggerglue'],
      entry_points=dict(console_scripts=['bevis=bevis_run:main']),
      zip_safe=False)





