import sys
import os
def daemonize (pidfile=None, user=None, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    if user is None:
        user = os.geteuid()

    # Perform first fork.
    try:
        pid = os.fork( )
        if pid > 0:
            sys.exit(0) # Exit first parent.
    except OSError, e:
        sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)
    # Decouple from parent environment.
    os.chdir("/")
    os.umask(0)
    os.setsid()
    # Perform second fork.
    try:
        pid = os.fork()
        if pid > 0:
            # Write out a pid file 
            if pidfile:
                with open(pidfile, 'w') as pidf:
                    pidf.write(str(pid))

            sys.exit(0) # Exit second parent.
    except OSError, e:
        sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)
    # The process is now daemonized, redirect standard file descriptors.
    for f in sys.stdout, sys.stderr:
        f.flush()


    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


    if user != os.geteuid():
        # You want to run as a different uid.
        if os.geteuid() == 0:
            # If you're root, fine. 
            os.seteuid(user)
        else:
            # If you're not root, no good.
            sys.stderr.write("Must be root to run daemon as a user other than yourself.\n")
            sys.exit(1)

