"""WARNING: This test module is butt-ugly.
"""
import os
import subprocess
import sys
import time
import zipfile
from os.path import dirname, getmtime, join

import lib537
from lib537.tests.fsfix import mk, attach_rm


SITE_PACKAGES = dirname(dirname(lib537.__file__))


def test_basic():
    mk( ('foo.py', "bar = 'Blah.'")
      , ('script', """\
import sys
import time
from os.path import dirname

sys.path.insert(0, '%s')
from lib537 import restarter

sys.path.insert(0, dirname(__file__))
import foo

def main():
    while 1:
        print foo.bar
        sys.stdout.flush()
        input = sys.stdin.readline()
        if input.strip():
            raise SystemExit(0)
        else:
            time.sleep(0.2)

        if restarter.should_restart():
            raise SystemExit(75)

if restarter.PARENT:
    restarter.launch_child()
else:
    main()
""" % SITE_PACKAGES))


    proc = subprocess.Popen( [sys.executable, join('fsfix', 'script')]
                           , stdin=subprocess.PIPE
                           , stdout=subprocess.PIPE
                           , stderr=subprocess.STDOUT
                            )

    expected = 'Blah.' + os.linesep
    actual = proc.stdout.readline()
    assert actual == expected, actual

    time.sleep(1.2) # figure on second-resolution modtimes
    open(join('fsfix', 'foo.py'), 'w+').write('bar = "BLAM!!!"')
    proc.stdin.write(os.linesep)
    expected = 'BLAM!!!' + os.linesep
    actual = proc.stdout.readline()
    assert actual == expected, actual


def test_non_module_files():
    mk( ('foo.py', "bar = 'Blah.'")
      , ('foo.conf', "[my conf file]")
      , ('script', """\
import sys
import time
from os.path import dirname, join

sys.path.insert(0, '%s')
from lib537 import restarter

sys.path.insert(0, dirname(__file__))
import foo

confpath = join(sys.path[0], 'foo.conf')
conf = open(confpath).read()

def main():
    restarter.track(confpath)
    while 1:
        print conf
        sys.stdout.flush()
        input = sys.stdin.readline()
        if input.strip():
            raise SystemExit(0)
        else:
            time.sleep(0.2)

        if restarter.should_restart():
            raise SystemExit(75)

if restarter.PARENT:
    restarter.launch_child()
else:
    main()
""" % SITE_PACKAGES))

    proc = subprocess.Popen( [sys.executable, join('fsfix', 'script')]
                           , stdin=subprocess.PIPE
                           , stdout=subprocess.PIPE
                           , stderr=subprocess.STDOUT
                            )

    expected = '[my conf file]' + os.linesep
    actual = proc.stdout.readline()
    assert actual == expected, actual

    time.sleep(1.2) # figure on second-resolution modtimes
    open(join('fsfix', 'foo.conf'), 'w+').write('[your conf file]')
    proc.stdin.write(os.linesep)
    expected = '[your conf file]' + os.linesep
    actual = proc.stdout.readline()
    assert actual == expected, actual


def test_zip_import():
    mk( ('foo.py', "bar = 'Blah.'")
      , ('script', """\
import sys
import time
from os.path import dirname, join

sys.path.insert(0, '%s')
from lib537 import restarter

sys.path.insert(0, join(dirname(__file__), 'foo.zip'))
import foo

def main():
    while 1:
        print foo.bar
        sys.stdout.flush()
        input = sys.stdin.readline()
        if input.strip():
            raise SystemExit(0)
        else:
            time.sleep(0.2)

        if restarter.should_restart():
            raise SystemExit(75)

if restarter.PARENT:
    restarter.launch_child()
else:
    main()
""" % SITE_PACKAGES))

    # Create the ZIP library archive.
    def create_zip_archive():
        pzf = zipfile.PyZipFile(join('fsfix', 'foo.zip'), 'w')
        pzf.writepy('fsfix')
        pzf.close()
        os.remove(join('fsfix', 'foo.py'))
        os.remove(join('fsfix', 'foo.pyc'))
    create_zip_archive()

    if 0: # use this to debug the subprocess
        proc = subprocess.Popen([sys.executable, join('fsfix', 'script')])
        proc.communicate()
        raise SystemExit


    proc = subprocess.Popen( [sys.executable, join('fsfix', 'script')]
                           , stdin=subprocess.PIPE
                           , stdout=subprocess.PIPE
                           , stderr=subprocess.STDOUT
                            )

    expected = 'Blah.' + os.linesep
    actual = proc.stdout.readline()
    assert actual == expected, actual

    time.sleep(1.2) # figure on second-resolution modtimes
    open(join('fsfix', 'foo.py'), 'w+').write('bar = 537')
    create_zip_archive() # ignored
    proc.stdin.write(os.linesep)
    expected = 'Blah.' + os.linesep
    actual = proc.stdout.readline()
    assert actual == expected, actual

attach_rm(globals(), 'test_')