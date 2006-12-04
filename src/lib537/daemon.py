"""Disk And Execution MONitor (daemon) support.

Daemonization is fundamental to computing, and proper techniques have by now
been well-established. Chad J. Schroeder provides a solid Python implementation
in his ASPN Python Cookbook recipe:

    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/278731

The present module is very lightly adapted from that original. The value added
is in API smoothing, documentation, and integration with PyPI and easy_install.

References:
    1) Advanced Programming in the Unix Environment: W. Richard Stevens
    2) Unix Programming Frequently Asked Questions:
         http://www.erlenstar.demon.co.uk/unix/faq_toc.html

"""
__author__ = "Chad J. Schroeder"
__copyright__ = "Copyright (C) 2005 Chad J. Schroeder"
__credits__ = "Chad Whitacre <chad@zetaweb.com>"
__version__ = "~~VERSION~~"


import os
import resource
import sys


# The standard I/O file descriptors are redirected to /dev/null by default.
if (hasattr(os, "devnull")):
    DEVNULL = os.devnull
else:
    DEVNULL = "/dev/null"


def become(umask=0, workdir='/', maxfd=1024, redirect_to=DEVNULL):
    """Daemonize the current process.

    When called, the current process will detach from any controlling terminal,
    and will run in the background as a daemon. The following options are
    available:

      umask         file mode creation mask of the daemon [0]
      workdir       working directory for the daemon [/]
      maxfd         default maximum number of available file descriptors [1024]
      redirect_to   new endpoint for the standard file descriptors [/dev/null]

    """

    try:
        # Fork a child process so the parent can exit.  This returns control to
        # the command-line or shell.  It also guarantees that the child will not
        # be a process group leader, since the child receives a new process ID
        # and inherits the parent's process group ID.  This step is required
        # to insure that the next call to os.setsid is successful.
        pid = os.fork()
    except OSError, e:
        raise Exception, "%s [%d]" % (e.strerror, e.errno)

    if (pid == 0):    # The first child.
        # To become the session leader of this new session and the process group
        # leader of the new process group, we call os.setsid().  The process is
        # also guaranteed not to have a controlling terminal.
        os.setsid()

        # Is ignoring SIGHUP necessary?
        #
        # It's often suggested that the SIGHUP signal should be ignored before
        # the second fork to avoid premature termination of the process.  The
        # reason is that when the first child terminates, all processes, e.g.
        # the second child, in the orphaned group will be sent a SIGHUP.
        #
        # "However, as part of the session management system, there are exactly
        # two cases where SIGHUP is sent on the death of a process:
        #
        #    1) When the process that dies is the session leader of a session that
        #        is attached to a terminal device, SIGHUP is sent to all processes
        #        in the foreground process group of that terminal device.
        #    2) When the death of a process causes a process group to become
        #        orphaned, and one or more processes in the orphaned group are
        #        stopped, then SIGHUP and SIGCONT are sent to all members of the
        #        orphaned group." [2]
        #
        # The first case can be ignored since the child is guaranteed not to have
        # a controlling terminal.  The second case isn't so easy to dismiss.
        # The process group is orphaned when the first child terminates and
        # POSIX.1 requires that every STOPPED process in an orphaned process
        # group be sent a SIGHUP signal followed by a SIGCONT signal.  Since the
        # second child is not STOPPED though, we can safely forego ignoring the
        # SIGHUP signal.  In any case, there are no ill-effects if it is ignored.
        #
        # import signal              # Set handlers for asynchronous events.
        # signal.signal(signal.SIGHUP, signal.SIG_IGN)

        try:
            # Fork a second child and exit immediately to prevent zombies.  This
            # causes the second child process to be orphaned, making the init
            # process responsible for its cleanup.  And, since the first child is
            # a session leader without a controlling terminal, it's possible for
            # it to acquire one by opening a terminal in the future (System V-
            # based systems).  This second fork guarantees that the child is no
            # longer a session leader, preventing the daemon from ever acquiring
            # a controlling terminal.
            pid = os.fork()    # Fork a second child.
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)

        if (pid == 0):    # The second child.
            # Since the current working directory may be a mounted filesystem, we
            # avoid the issue of not being able to unmount the filesystem at
            # shutdown time by changing it to the root directory.
            os.chdir(workdir)
            # We probably don't want the file mode creation mask inherited from
            # the parent, so we give the child complete control over permissions.
            os.umask(umask)
        else:
            # exit() or _exit()?  See below.
            os._exit(0)    # Exit parent (the first child) of the second child.
    else:
        # exit() or _exit()?
        # _exit is like exit(), but it doesn't call any functions registered
        # with atexit (and on_exit) or any registered signal handlers.  It also
        # closes any open file descriptors.  Using exit() may cause all stdio
        # streams to be flushed twice and any temporary files may be unexpectedly
        # removed.  It's therefore recommended that child branches of a fork()
        # and the parent branch(es) of a daemon use _exit().
        os._exit(0)    # Exit parent of the first child.

    # Close all open file descriptors.  This prevents the child from keeping
    # open any file descriptors inherited from the parent.  There is a variety
    # of methods to accomplish this task.  Three are listed below.
    #
    # Try the system configuration variable, SC_OPEN_MAX, to obtain the maximum
    # number of open file descriptors to close.  If it doesn't exists, use
    # the default value (configurable).
    #
    # try:
    #     maxfd = os.sysconf("SC_OPEN_MAX")
    # except (AttributeError, ValueError):
    #     maxfd = MAXFD
    #
    # OR
    #
    # if (os.sysconf_names.has_key("SC_OPEN_MAX")):
    #     maxfd = os.sysconf("SC_OPEN_MAX")
    # else:
    #     maxfd = MAXFD
    #
    # OR
    #
    # Use the getrlimit method to retrieve the maximum file descriptor number
    # that can be opened by this process.  If there is not limit on the
    # resource, use the default value.

    nofile = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (nofile == resource.RLIM_INFINITY):
        nofile = maxfd

    # Iterate through and close all file descriptors.
    for fd in range(0, nofile):
        try:
            os.close(fd)
        except OSError:    # ERROR, fd wasn't open to begin with (ignored)
            pass

    # Redirect the standard I/O file descriptors to the specified file.  Since
    # the daemon has no controlling terminal, most daemons redirect stdin,
    # stdout, and stderr to /dev/null.  This is done to prevent side-effects
    # from reads and writes to the standard I/O file descriptors.

    # This call to open is guaranteed to return the lowest file descriptor,
    # which will be 0 (stdin), since it was closed above.
    os.open(redirect_to, os.O_RDWR)    # standard input (0)

    # Duplicate standard input to standard output and standard error.
    os.dup2(0, 1)            # standard output (1)
    os.dup2(0, 2)            # standard error (2)

    return(0)


# Test
# ====

if __name__ == "__main__":
    """Test/demonstrate the module.

    The following will create a new file in the current directory, containing a
    number of daemon-related process parameters. In particular, notice the
    relationship between the daemon's process ID, process group ID, and its
    parent's process ID.

    """

    retCode = become(workdir='.')

    procParams = """
    return code = %s
    process ID = %s
    parent process ID = %s
    process group ID = %s
    session ID = %s
    user ID = %s
    effective user ID = %s
    real group ID = %s
    effective group ID = %s
    """ % (retCode, os.getpid(), os.getppid(), os.getpgrp(), os.getsid(0),
    os.getuid(), os.geteuid(), os.getgid(), os.getegid())

    open("daemon.log", "w").write(procParams + "\n")

    sys.exit(retCode)


# Legal
# =====

"""
The original module is (c) 2005 by Chad J. Schroeder, and is used here under
"the Python license," per ASPN's notice:

    Except where otherwise noted, recipes in the Python Cookbook are published
    under the Python license <http://www.python.org/license>.

My changes are:

    Copyright (c) 2006 Chad Whitacre <chad@zetaweb.com>

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to
    use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
    the Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
    FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
    COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
    IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
    CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    <http://opensource.org/licenses/mit-license.php>

"""