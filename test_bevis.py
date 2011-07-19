#!/usr/bin/env python2.7
import datetime
import os
from loggerglue.emitter import TCPSyslogEmitter
from loggerglue.logger import Logger
from loggerglue.rfc5424 import SyslogEntry, SDElement
import unittest2 as unittest

class TestBevis(unittest.TestCase):
    def test_tcp_msg_handle(self):
        """A functional test that emits a syslog message to an 
        assumed-running bevis instance at localhost:6514.

        """
        y = SyslogEntry( prival=165,
                        timestamp=datetime.datetime.utcnow(),
                        hostname='myhost',
                        app_name='my_app',
                        procid=os.getpid(),
                        msgid='ID42',
                        structured_data=[SDElement('exampleSDID@32473',
                                        [('iut','3'),
                                        ('eventSource','Application'),
                                        ('eventID','1011'),
                                        ('eventID','1012')]
                                        )],
                        msg='An application event log entry through TCP'
                       )
        client = TCPSyslogEmitter(address=('127.0.0.1', 6514), octet_based_framing=False)
        client.emit(y)


if __name__ == '__main__':
    unittest.main()
