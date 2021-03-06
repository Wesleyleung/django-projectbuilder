#!/usr/bin/env python
#
#   Original Authors:
#   Steve Phillips -- steve@builtbyptm.com
#   AJ v Bahnken   -- aj@builtbyptm.com
#
#   Custom Version
#   Kevin Xu       -- kevin@imkevinxu.com

#
#   Requires virtualenv, virtualenvwrapper, and git
#

import os
import random
import re
import shutil
import string
import sys

from subprocess import Popen, call, STDOUT, PIPE


def which(program):

    import os

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

try:
    import argparse
except ImportError:
    print "argparse not installed. Please install with\n"
    print "    sudo pip install argparse\n"
    print "then re-run this script."
    sys.exit(1)


# If user is in a virtualenv, tell them to get out first
if hasattr(sys, 'real_prefix'):
    print "You're already in a virtualenv. Type\n"
    print "    deactivate\n"
    print "to leave, then run this script again."
    sys.exit(1)

VIRTUALENV_WRAPPER_PATH = which('virtualenvwrapper.sh')
if VIRTUALENV_WRAPPER_PATH is None:
    VIRTUALENV_WRAPPER_PATH = '/usr/local/bin/virtualenvwrapper.sh'

if not os.path.isfile(VIRTUALENV_WRAPPER_PATH):
    cmd = 'echo $VIRTUALENV_WRAPPER_PATH'
    output = call(cmd, shell=True)
    if output:
        VIRTUALENV_WRAPPER_PATH = output
    else:
        print "We can not seem to find virtualenvwrapper\n"
        print "Either install it through pip\n"
        print "     sudo pip install virtualenvwrapper\n"
        print "or set $VIRTUALENV_WRAPPER_PATH to the location of\n"
        print "virtualenvwrapper on your machine."
        sys.exit(1)

# We have what we need! Let's do this...

DPB_PATH = os.path.abspath(os.path.dirname(__file__)) + '/'
DJANGO_FILES_PATH = DPB_PATH + 'django-files/'

# These are the arguments for the builder.  We can extend the
# arguments as we want to add more functionality
parser = argparse.ArgumentParser(description='''PTM Web Engineering presents
                                 Django Project Builder''')

# Simple arguments
parser.add_argument('--version', '-v', action='version',
                    version='Django Project Builder v0.1')
parser.add_argument('--path', action='store', dest='path',
                    help='''Specifies where the new Django project
                    should be made, including the project name at the
                    end (e.g. /home/username/code/project_name)''',
                    required=True)
parser.add_argument('-q', '--quiet', action='store_true', default=False,
                    help='''Quiets all output except the finish message.''',
                    dest='quiet')

# Theme arguments
parser.add_argument('--bootstrap', action='store_true', default=False,
                    help='''This will include Bootstrap as the template
                    and media base of the project.''', dest='bootstrap')
parser.add_argument('--foundation', action='store_true', default=False,
                    help='''This will include Foundation 3 as the template
                    and media base of the project.''', dest='foundation')

# Extra Packages
parser.add_argument('--bcrypt', action='store_true', default=False,
                    help='''This will install py-bcrypt and use bcrypt
                    as the main password hashing for the project.''', dest='bcrypt')
parser.add_argument('--debug', action='store_true', default=False,
                    help='''This will install the Django Debug Toolbar
                    package for the project.''', dest='debug')
parser.add_argument('--jinja2', action='store_true', default=False,
                    help='''This will install Jinja2 and Coffin as the default
                    templating engine of the project.''', dest='jinja2')

# SUPER Argument for imkevinxu
parser.add_argument('--imkevinxu', action='store_true', default=False,
                    help='''Super argument with default packages for imkevinxu
                    including Foundation, Jinja2 and Debug Toolbar.''',
                    dest='imkevinxu')

arguments = parser.parse_args()

# All arguments that imkevinxu enables
if arguments.imkevinxu:
    arguments.foundation = True
    arguments.jinja2 = True
    arguments.bcrypt = True
    arguments.debug = True


def check_projectname():
    if not re.search(r'^[_a-zA-Z]\w*$', PROJECT_NAME):
        message = 'Error: \'%s\' is not a valid project name. Please ' % PROJECT_NAME
        if not re.search(r'^[_a-zA-Z]', PROJECT_NAME):
            message += ('make sure the name begins '
                        'with a letter or underscore.')
        else:
            message += 'use only numbers, letters and underscores.'

        sys.exit(message)

from extra_settings import *


def copy_files(folder_path, file_types, pathify):
    """Copies the contents of django_files and server_scripts, and
    performs string interpolations (e.g., %(APP_NAME)s => 'myapp')"""
    for filename in file_types:
        # Grab *-needed filenames
        f_read = open(folder_path + filename, 'r')
        contents = f_read.read()
        f_read.close()
        # Replace %(SECRET_KEY)s, etc with new value for new project
        if filename.endswith('-needed'):
            new_filename = filename.replace('-needed', '')
        # Loop through list of locations new_filename should be placed
        for dir in pathify[new_filename]:
            # Path names include '%(PROJECT_NAME)s', etc
            file_path = dir % replacement_values
            f_write = open(PROJECT_PATH + file_path + new_filename, 'a')
            new_contents = contents % replacement_values

            # Appends certain attributes and settings to some django files for
            # various extra packages according to the arguments
            if arguments.bcrypt and new_filename in bcryptify_files:
                new_contents = bcryptify(new_contents, new_filename)
            if arguments.debug and new_filename in debugify_files:
                new_contents = debugify(new_contents, new_filename)
            if arguments.jinja2 and new_filename in jinjaify_files:
                new_contents = jinjaify(new_contents, new_filename)
                if new_filename == 'appurls.py':
                    new_contents = new_contents % replacement_values

            # Justifies the spacing for comments in code in README.md
            if new_filename == "README.md":
                new_contents = justify(new_contents)

            f_write.write(new_contents)
            f_write.close()


def sh(cmd):
    return Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE).communicate()[0]

# Maps cleaned filenames to where each file should be copied relative
# to PROJECT_PATH
django_pathify = {
    '.gitignore':                   [''],
    '__init__.py':                  ['%(PROJECT_NAME)s/', '%(APP_NAME)s/'],
    'admin.py':                     ['%(APP_NAME)s/'],
    'appurls.py':                   ['%(APP_NAME)s/'],
    'django.wsgi':                  ['apache/'],
    'forms.py':                     ['%(APP_NAME)s/'],
    'jinja2.py':                    ['%(PROJECT_NAME)s/'],
    'manage.py':                    [''],
    'model_forms.py':               ['%(APP_NAME)s/'],
    'models.py':                    ['%(APP_NAME)s/'],
    'notes.txt':                    [''],
    'README.md':                    [''],
    'requirements.txt':             [''],
    'settings.py':                  ['%(PROJECT_NAME)s/'],
    'settings_local.py':            ['%(PROJECT_NAME)s/'],
    'tests.py':                     ['%(APP_NAME)s/'],
    'urls.py':                      ['%(PROJECT_NAME)s/'],
    'views.py':                     ['%(APP_NAME)s/'],
    'wsgi.py':                      ['%(PROJECT_NAME)s/'],
}

# Trailing / may be included or excluded up to this point
PROJECT_PATH = arguments.path.rstrip('/') + '/'
PROJECT_NAME = PROJECT_PATH.split('/')[-2].split('_')[0]  # Before the '/'
APP_NAME     = PROJECT_NAME + '_app'
BASE_PATH    = '/'.join(PROJECT_PATH.split('/')[:-2]) + '/'

# ADMIN INFORMATION
ADMIN_NAME  = os.environ.get("ADMIN_NAME") if os.environ.get("ADMIN_NAME") else 'Agent Smith'
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL") if os.environ.get("ADMIN_EMAIL") else 'admin@example.com'

# TODO
# vewrapper = pbs.which('virtualenvwrapper.sh')
# vewrapper("")

SECRET_KEY = ''.join([random.choice(string.printable[:94].replace("'", ""))
                      for _ in range(50)])
PROJECT_PASSWORD = ''.join([random.choice(string.printable[:62])
                            for _ in range(30)])

# Defines key: value pairs so that
#   '%(PROJECT_NAME)s' % replacement_values
# evaluates to the value of the `PROJECT_NAME` variable, such as
#   'my_project_name'
replacement_values = {
    'PROJECT_NAME':     PROJECT_NAME,
    'PROJECT_NAME_CAP': PROJECT_NAME.capitalize(),
    'APP_NAME':         APP_NAME,
    'PROJECT_PASSWORD': PROJECT_PASSWORD,
    'BASE_PATH':        BASE_PATH,
    'SECRET_KEY':       SECRET_KEY,
    'PROJECT_PATH':     PROJECT_PATH,
    'ADMIN_NAME':       ADMIN_NAME,
    'ADMIN_EMAIL':      ADMIN_EMAIL,
}

# Doing it this way so DPB can add 'extra_settings' on the fly.
needed_dirs = ['static', 'apache', '%(PROJECT_NAME)s', '%(APP_NAME)s']

# Make sure PROJECT_NAME follows Django's restrictions
check_projectname()

if not arguments.quiet:
    print "Creating directories..."

# Use 'git init' to create the PROJECT_PATH directory and turn it into
# a git repo
cmd = 'bash -c "git init %s"' % PROJECT_PATH
output = sh(cmd)

if not arguments.quiet:
    print '\n', output, '\n'

# Create all other dirs (each a sub-(sub-?)directory) of PROJECT_PATH
for dir_name in needed_dirs:
    os.mkdir(PROJECT_PATH + dir_name % replacement_values)

# Build list of all django-specific files to be copied into new project.
django_files = [x for x in os.listdir(DJANGO_FILES_PATH)
                if x.endswith('-needed')]
if not arguments.jinja2:
    django_files.remove('jinja2.py-needed')

if not arguments.quiet:
    print "Creating django files..."

# Oddly-placed '%' in weird_files screws up our string interpolation,
# so copy these files verbatim
copy_files(DJANGO_FILES_PATH, django_files, django_pathify)

if not arguments.quiet:
    print "Copying directories..."

# Add directory names here
generic_dirs = ['media', 'templates']
generic_dirs = [DPB_PATH + d for d in generic_dirs]

for dirname in generic_dirs:
    # cp -r media-generic $PROJECT_PATH/media && cp -r templates-generic ...
    new_dir = PROJECT_PATH + dirname.split('/')[-1]
    if arguments.bootstrap:
        shutil.copytree(dirname + '-bootstrap', new_dir)
    elif arguments.foundation:
        shutil.copytree(dirname + '-foundation', new_dir)
    else:
        shutil.copytree(dirname + '-generic', new_dir)

template_needs_replacements = ['base.html', 'index.html', 'template.html', 'login.html', '500.html']

# Replace %(VARIABLES)s with right values for templates
# Loop through list of templates that should be replaced
templates_dir = PROJECT_PATH + 'templates/'
for template in template_needs_replacements:
    f_read = open(templates_dir + template, 'r')
    contents = f_read.read()
    f_read.close()

    f_write = open(templates_dir + template, 'w')
    for key, value in replacement_values.items():
        contents = contents.replace('%(' + key + ')s', value)

    if arguments.foundation:
        if arguments.bcrypt and template in bcryptify_files:
            contents = bcryptify(contents, template)
        if arguments.debug and template in debugify_files:
            contents = debugify(contents, template)
        if arguments.jinja2 and template in jinjaify_template_files:
            contents = jinjaify_templates(contents, template)

    f_write.write(contents)
    f_write.close()

if not arguments.quiet:
    print "Making virtualenv..."

cmd  = 'bash -c "source %s &&' % VIRTUALENV_WRAPPER_PATH
cmd += ' mkvirtualenv %s"' % PROJECT_NAME

output = sh(cmd)

if not arguments.quiet:
    print '\n', output, '\n'

## The below part is made much faster with a small requirements.txt.
## We have the options to include more packages, which in turn
## will take long, but of course is needed. This allows for making
## projects which need only the basics, and ones that need a lot.

if not arguments.quiet:
    print "Running 'pip install -r requirements.txt'. This could take a while...",
    print "(don't press control-c!)"

# FIXME Shouldn't assume the location of virtualenvwrapper.sh
cmd  = 'bash -c "source %s && workon' % VIRTUALENV_WRAPPER_PATH
cmd += ' %(PROJECT_NAME)s && cd %(PROJECT_PATH)s &&' % replacement_values
cmd += ' pip install -r requirements.txt && pip freeze > requirements.txt"'

output = sh(cmd)

if not arguments.quiet:
    print '\n', output, '\n'

# virtualenv now exists

if not arguments.quiet:
    print "Creating git repo..."

cmd  = 'bash -c "cd %s &&' % PROJECT_PATH
cmd += ' git add . && git commit -m \'first commit\'"'
output = sh(cmd)

if not arguments.quiet:
    print '\n', output, '\n'

print "\nDone! Now run\n"
print "    cd %(PROJECT_PATH)s && workon %(PROJECT_NAME)s &&" % replacement_values,
print "python manage.py syncdb\n\nGet to work!"
