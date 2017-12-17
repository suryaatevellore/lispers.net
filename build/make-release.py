#
# make-release.py
#
# This python script will do a release of the lispers.net LISP code.
#

import os
import commands
import sys
import time
import platform

#------------------------------------------------------------------------------

obfuscate_on = True
root = "./.." if os.path.exists("./.git") else "~/code"

#
# First check that this is running in the build directory and that peer
# directories "lisp" and "docs" exist.
#
curdir = commands.getoutput("pwd")
curdir = curdir.split("/")
if (curdir[-1] != "build"):
    print "Need to be in directory named 'build'"
    exit(1)
#endif
if (os.path.exists("../lisp") == False):
    print "Directory '../lisp' needs to be a peer directory"
    exit(1)
#endif
if (os.path.exists("../docs") == False):
    print "Directory '../docs' needs to be a peer directory"
    exit(1)
#endif

#
# Second check if we can build on this machine.
#
machine = platform.machine()
if (machine.find("x86") != -1):
    cpu = "x86"
elif (machine.find("mips") != -1):
    cpu = "mips"
else:
    print "Build does not support cpu type {}".format(machine)
    exit(1)
#endif

start_time = time.time()
build_date = commands.getoutput("date")

#
# Run pyflakes. We don't want to build a release with python errors.
#
status = os.system("pyflakes {}/lisp/*py > /dev/null".format(root))
if (status != 0):
    print("Found pyflakes errors")
    exit(1)
#endif

#
# Check and ask if you want to build release with debug code in it.
#
command = 'egrep "debug\(" {}/lisp/*py | egrep -v "def|self" > /dev/null'. \
    format(root)
status = os.system(command)
if (status == 0):
    if (raw_input("Build release with debug code? (y/n): ") != "y"): exit(1)
#endif

if (len(sys.argv) > 1): 
    version = sys.argv[1]
else:
    version = raw_input("Enter version number (in format x.y): ")
#endif

dir = "release-{}".format(version)
status = os.system("mkdir " + dir)
if (status != 0):
    print "Could not create directory {}".format(dir)
    exit(1)
#endif
os.system("rm latest; ln -sf {} latest".format(dir)) 

print "Copying files from ../lisp to " + dir + " build directory ...",
command = '''
cp ../lisp/lispapi.txt ../lisp/*py ../lisp/*-LISP ../lisp/RL-* ../lisp/*.pem.default ../lisp/release-notes.txt ../lisp/pslisp ../lisp/lispers.net-geo.html ./{}/.
'''.format(dir)

status = os.system(command)
if (status != 0):
    print "failed"
    exit(1)
#endif
print "done"

print "Copying install scripts to " + dir + " build directory ...",
command = "cp ./py-depend/lispers.net-test-install.py ./{}/.".format(dir)
status = os.system(command)
if (status != 0):
    print "failed"
    exit(1)
#endif
command = "cp ./py-depend/lispers.net-install-ubuntu.py ./{}/.".format(dir)
status = os.system(command)
if (status != 0):
    print "failed"
    exit(1)
#endif

print "done"

#
# Move *.py files to src directory. We will obfuscate the source files in
# the main release directory and then compile them.
#
os.system("mkdir {}/src; mv {}/*py {}/src/.".format(dir, dir, dir))

#
# Obfuscate the py files. They are put in directory ./ob.
#
if (obfuscate_on):
    py_files = commands.getoutput("cd {}/src; ls *py".format(dir)).split("\n")
    libraries = ["lisp.py", "lispconfig.py", "lispapi.py", "chacha.py",
        "poly1305.py"]
    for py_file in py_files:
        print "Obfuscating {} ... ".format(py_file)
        dash_a = "-a" if py_file in libraries else ""
        os.system("pyobfuscate {} {}/src/{} > {}/{}".format(dash_a, dir, 
            py_file, dir, py_file))
    #endfor
else:
    os.system("cp {}/src/*py {}/.".format(dir, dir))
#endif

#
# Do the compile.
#
print "Compiling for machine '{}'".format(machine)
status = os.system("cd ./{}; python -O -m compileall *py".format(dir))
if (status != 0):
    print "Compilation failed"
    exit(1)
#endif

#
# Put obfuscated files in the ob/ directory.
#
if (obfuscate_on):
    os.system("mkdir {}/ob; mv {}/*py {}/ob/".format(dir, dir, dir))
else:
    os.system("rm -fr {}/*py".format(dir))
#endif

#
# Put the version and date file in the directory.
#
os.system('cd ./{}; echo "{}" > lisp-version.txt'.format(dir, version))
os.system('cd ./{}; echo "{}" > lisp-build-date.txt'.format(dir, build_date))
os.system('cp ../docs/lisp.config.example ./{}/.'.format(dir))
os.system('cp ../docs/how-to-install.txt ./{}/.'.format(dir))
os.system('cp ./py-depend/get-pip.py ./{}/.'.format(dir))
os.system('cp ./py-depend/pip-requirements.txt ./{}/.'.format(dir))

#
# Now tar and gzip files for release.
#
tar_file = "lispers.net-" + cpu + "-" + dir + ".tgz"
print "Build tgz file {} ... ".format(tar_file),
files = "*.pyo *.txt lisp.config.example lisp-cert.pem.default *-LISP " + \
    "RL-* get-pip.py pslisp lispers.net-geo.html"
command = "cd {}; tar czf {} {}".format(dir, tar_file, files)
status = os.system(command)
if (status != 0):
    print "failed"
    exit(1)
#endif
print "done"

#
# Put pyo files in the bin/ directory.
#
os.system("mkdir {}/bin; mv {}/*pyo {}/bin/".format(dir, dir, dir))

print "Copying version information to ../lisp directory ... ", 
command = '''
    cd ./{}; 
    cp lisp-version.txt ../../lisp/.;
    cp lisp-build-date.txt ../../lisp/.;
    chmod -R 555 *;
    chmod 444 lispers.net*tgz;
    cd ../;
'''.format(dir)
status = os.system(command)
if (status != 0):
    print "failed"
    exit(1)
#endif
print "done"

elapsed = round(time.time() - start_time, 3)
print "Script run time: {} seconds".format(elapsed)
exit(0)

#------------------------------------------------------------------------------