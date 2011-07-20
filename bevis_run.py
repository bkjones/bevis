#!/usr/bin/env python2.7
import logging
import os
from tornado import ioloop
from bevis import Bevis
import yaml
import argparse
from bevis import version
from bevis.daemonize import daemonize

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

    parser.add_argument('-u', '--user',
                        action='store',
                        dest='user',
                        default=os.geteuid())

    parser.add_argument('-p', '--pidfile',
                        action='store',
                        dest='pidfile',
                        default='/tmp/bevis.pid')

    parser.add_argument('-f', '--foreground',
                        action='store_true',
                        dest='foreground',
                        default=False)

    args = parser.parse_args()
    return args

def main():
    args = do_args()
    with open(args.config) as cfgpath:
        config = yaml.load(cfgpath)

    logging.basicConfig(level=log_levels[config['Server']['log-level']],
                        filename=config['Server']['log-filename'])



    if not args.foreground:
        daemonize(user=int(args.user), pidfile=args.pidfile, stderr='/dev/stdout', stdout='/dev/stdout')

    bevis = Bevis(config)
    # this line moved to post-fork because kqueue objects don't live across
    # forks, and someone might run this on a mac for testing or something.
    bevis.listen(config['Server']['port'])
    ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
