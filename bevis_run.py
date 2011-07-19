#!/usr/bin/env python2.7
import logging
from tornado import ioloop
from bevis import Bevis
import yaml
import argparse
from bevis import version
log_levels = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

def do_args():
    parser = argparse.ArgumentParser(prog='bevis',
                                     description='A syslog-to-AMQP bridge')
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s '+'.'.join(str(i) for i in version))

    parser.add_argument('-c', '--config',
                        action='store',
                        dest='config',
                        required=True)

    args = parser.parse_args()
    return args

def main():
    args = do_args()
    with open(args.config) as cfgpath:
        config = yaml.load(cfgpath)

    #    config = {'Server': {'port': 6514,
    #                        'log-level': logging.DEBUG,
    #                        'log-filename': 'bevis.log'},
    #              'AMQP': {'username': 'guest',
    #                       'password': 'guest',
    #                       'vhost': '/',
    #                       'host': 'localhost'}}
    logging.basicConfig(level=log_levels[config['Server']['log-level']],
                        filename=config['Server']['log-filename'])
    bevis = Bevis(config)
    bevis.listen(config['Server']['port'])

    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        bevis.stop()

if __name__ == '__main__':
    main()
