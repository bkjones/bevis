#!/usr/bin/env python

"""
A syslog receiver that queues messages to an AMQP broker.
"""

import errno
import json
import socket
import logging
import pika
from tornado import ioloop, httpserver
from loggerglue.rfc5424 import SyslogEntry

class Bevis(httpserver.HTTPServer):
    """
    bevis = bevis_server.Bevis(config)
    bevis.listen(config["Server"]["port"])

    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        bevis.stop()

    """
    def __init__(self, config):
        self.io_loop = None
        self._socket = None
        self._started = False
        self.config = config

        self._sockets = {}
        self._log = logging.getLogger()
        self._log.debug("Logging is set to debug")
        self.setup()

    def setup(self):
        """Sets up the AMQP connection and channel. These both 
        eventually are passed to bevis_connection for use in actually
        publishing the syslog messages to the broker. 

        TODO: Clean up those except blocks. Yuk!
        """

        def pika_on_connected(connection):
            try:
                logging.debug("Getting channel from connection...")
                connection.channel(pika_on_channel_open)
            except Exception as out:
                logging.debug(out)

        def pika_on_channel_open(channel):
            try:
                self.pika_channel = channel
                logging.debug("Set up self.pika_channel %s", self.pika_channel)
            except Exception as out:
                logging.debug(out)


        credentials = pika.PlainCredentials(self.config["AMQP"]["username"], 
                                            self.config["AMQP"]["password"])

        parameters = pika.ConnectionParameters(self.config["AMQP"]["host"], 
                                 virtual_host = self.config["AMQP"]["vhost"],
                                 credentials=credentials)

        try:
            pika.adapters.tornado_connection.TornadoConnection(
                parameters, pika_on_connected)
            logging.debug("Set up TornadoConnection")
        except Exception as out:
            logging.debug(out)

    def stop(self):
        """Server Shutdown"""
        self._socket.close()

    def _handle_events(self, fd, events):
        """Accept a new connection -- starts BevisConnection"""
        while True:
            try:
                connection, address = self._sockets[fd].accept()
            except socket.error as e:
                if e.args[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return
                raise

            # Start a new BevisConnection
            BevisConnection(connection,
                            address,
                            self.io_loop,
                            self.pika_channel,
                            self.config['AMQP']['topic_exch'],
                            self.config['AMQP']['rt_key_components'])


def get_severity_and_facility(syslog_dict):
    """
    Parses the rfc5424 'prival' in the dict to derive
    the severity and facility of the message, maps them to human-readable
    words, and adds those keys to the dictionary.

    """
    sev_words = {0: 'emerg',
                 1: 'alert',
                 2: 'crit',
                 3: 'err',
                 4: 'warn',
                 5: 'notice',
                 6: 'info',
                 7: 'debug'}

    fac_words = {0: 'kern',
                 1: 'user',
                 2: 'mail',
                 3: 'daemon',
                 4: 'auth',
                 5: 'syslog',
                 6: 'lpr',
                 7: 'news',
                 8: 'uucp',
                 9: 'clock',
                 10: 'authpriv',
                 11: 'ftp',
                 12: 'ntp',
                 13: 'logaudit',
                 14: 'logalert',
                 15: 'clock2',
                 16: 'local0',
                 17: 'local1',
                 18: 'local2',
                 19: 'local3',
                 20: 'local4',
                 21: 'local5',
                 22: 'local6',
                 23: 'local7'}

    prival = syslog_dict['prival']
    if not prival:
        return syslog_dict

    severity = prival & 7
    facility = (prival - severity) / 8
    syslog_dict['severity'] = sev_words[severity]
    syslog_dict['facility'] = fac_words[facility]
    return syslog_dict

class BevisConnection(object):
    """Takes each message coming into bevis_server and (asynchronously) sends
    it along to the AMQP broker.

    It is assumed that the AMQP exchange is set up and properly bound
    to a queue. No binding happens here.

    It is also assumed that all log messages are < 4096 bytes in length.
    """

    def __init__(self, socket, address, io_loop, pika_channel,
                 topic_exch, rt_key_components):
        """
        Adds itself to the tornado ioloop, puts together an
        AMQP message, and publishes it.

        """
        self.read_chunk_size = 4096
        self.socket = socket
        self.socket.setblocking(False)
        self.fileno = socket.fileno()
        self.address = address
        self.pika_channel = pika_channel
        self.topic_exch = topic_exch
        self.rt_key_components = rt_key_components

        # setup io loop
        self.io_loop = io_loop
        self.io_loop.add_handler(self.fileno, self._handle_events,
                                 self.io_loop.READ | self.io_loop.ERROR)

        logging.info("New connection [%s]: %s", self.fileno, str(self.address))

    def _handle_events(self, fd, events):
        if not self.socket:
            logging.warning("Got events for closed stream %d", fd)
            return
        if events & self.io_loop.READ:
            self._handle_read()
        if events & self.io_loop.ERROR:
            self._close_socket()
            return

    def _close_socket(self):
        """Closes socket and removes it from epoll and FlockServer"""
        try:
            self.io_loop.remove_handler(self.fileno)
        except:
            pass

        if self.socket:
            self.socket.close()
            self.socket = None

    def _handle_read(self):
        """Signal by epoll: data chunk ready to read from socket buffer."""
        try:
            chunk = self.socket.recv(self.read_chunk_size)
        except socket.error as e:
            if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                return
            else:
                print "Read error on %d: %s" % (self.fileno, e)
                self._close_socket()
                return

        if not chunk or not chunk.strip():
            logging.info("empty chunk. closing socket")
            self._close_socket()
            return

        self._process_request(chunk)
        logging.debug("Read handled. All done.")

    def _process_request(self, request):
        """Processing of the log entry. Later this will do more work"""
        syslog_dict = {}
        try:
            logging.debug("INCOMING REQ: %s" % request)
            syslog_entry = SyslogEntry.from_line(request)
            syslog_dict = syslog_entry.__dict__
            syslog_dict = get_severity_and_facility(syslog_dict)
        except Exception as out:
            logging.error(out)

        logging.debug("Processing request...")
        self.send_to_amqp(syslog_dict)

    def send_to_amqp(self, syslog_dict):
        """
        Send request to AMQP broker.
        """
        rt_key = '.'.join([syslog_dict[i] for i in self.rt_key_components])
        logging.debug("Sending amqp message")
        syslog_json = json.dumps(syslog_dict, default=str)
        logging.debug("Sending to AMQP: %s", syslog_json)

        # Send via pika
        logging.debug("RT KEY: %s EXCH: %s", rt_key, self.topic_exch)
        self.pika_channel.basic_publish(exchange=self.topic_exch,
              routing_key=rt_key,
              body=syslog_json)

