================
Bevis
================


What is it?
--------------

It's a syslog listener that forwards messages to AMQP (RabbitMQ, specifically).
So, you can tell rsyslog to send messages to Bevis, and tell Bevis how you want
it to act with regards to sending the messages on to an AMQP server. Namely, you 
can tell it what components of the syslog message to use in building a routing key 
for the message.

What's with the name?
----------------------

I wanted to call it 'lumberjack', since it deals with logs. Too hard to find in
a Google search and a pretty common software project name. 

Then I thought 'logue', since it's a combination of 'log' and 'queue'. Just
thought I could do better. 

Bevis is the name of a rather interesting lumberjack from a Monty Python skit
(bevis is written in Python, which is named after Monty Python). See the skit:
http://www.youtube.com/watch?v=mL7n5mEmXJo

What's required?
--------------------------
Python 2.7 (I use argparse)
An rfc5424-compliant syslog source (I test with rsyslog)
pika (I test with 0.9.5)
tornado (I test with 2.0git)
loggerglue (I test with 1.0)

Blindingly Fast Start
----------------------

::
  $ git clone http://github.com/bkjones/bevis.git
  $ cd bevis
  $ python setup.py install
  $ bevis -c etc/config.yaml -f # run in the foreground

*Open another terminal*

::
  $ python test_bevis.py
  $ tail bevis.log

You should see an attempt to publish the message, and the message itself in the log.
If you have a RabbitMQ server running on localhost, *and* you have an exchange set up 
*and* a queue bound to it as specified in config.yaml, there should be a message in 
your queue.

What's rfc5424, and how do I know if I'm compliant?
-----------------------------------------------------

RFC 5424 defines the syslog protocol. Oddly, it seems difficult to find
compliant applications. In some cases it's hard to even verify compliance:
Linux syslogd's man page (and related ones like syslog.conf and syslog)
don't mention what RFC it is compliant with. So, to be completely honest, I
don't (yet) have a bullet-proof answer for you on how to tell if you're
compliant. 

I *can* tell you that I test with rsyslog and it is *able* to forward syslog
messages from whatever application it gets them from, to Bevis, in rfc5424
format. Here's the line in my rsyslog configuration that does the trick: 

*.*  @@127.0.0.1:6514;RSYSLOG_SyslogProtocol123Format

This is a test setup wherein I forward a copy of everything (*.*) to a Bevis
server on the localhost (127.0.0.1) listening on port 6514. After the
semicolon is the name of an rsyslog 'template'.

The '23' in the template name refers to
http://tools.ietf.org/html/draft-ietf-syslog-protocol-23, which it appears
is obsoleted by rfc5424, which itself seems to be a bugfix update to 23.
Don't quote me on that.



