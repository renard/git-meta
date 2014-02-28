#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
# git-meta --- Handle file metadata in git

"""

# Copyright © 2014 Sébastien Gross <seb•ɑƬ•chezwam•ɖɵʈ•org>
# Created: 2014-02-26
# Last changed: 2014-02-28 16:58:36

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.


__author__ = "Sébastien Gross"
__copyright__ = """Copyright © 2014 Sébastien Gross <seb•ɑƬ•chezwam•ɖɵʈ•org>"""

import os, sys, subprocess
import pipes
from stat import *
import pwd
import grp
import json
import argparse
import pprint


def run(cmd):
    """run cmd"""
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    proc.wait()
    out, err = proc.communicate()
    rc = proc.returncode
    if rc == 0:
        return out
    else:
        sys.stdout.write("Failed (%s): %s\n" %
                         (rc, ' '.join(pipes.quote(arg) for arg in cmd)))
        sys.stderr.write(err)
        sys.exit(1)


def git_get_files_attributs(args):
    """ """
    out = run(['git', 'ls-files', '-z'])
    files=out.split('\0')
    files.sort()
    rows = []
    for f in files:
        if not(os.path.isfile(f)):
            continue
        row = [ f ]
        st = os.stat(f)
        row += [ st.st_mode, st.st_mtime ]
        if args['numeric_owner'] is True:
            row += [ st.st_uid, st.st_gid ]
        elif args['owner'] is True:
            row += [pwd.getpwuid(st.st_uid).pw_name,
                    grp.getgrgid(st.st_gid).gr_name]
        rows.append(row)
    metadata = open(args['data'], 'w')
    json.dump(rows, metadata, indent=0)
    metadata.close()

def load_metadata(args):
    """Load metada from file"""
    p = open(args['data'], 'r')
    ret = json.load(p)
    p.close()
    return ret

def git_set_file_attributs(args):
    rows = load_metadata(args)
    for row in rows:
        if args['skip_perms'] is False:
            os.chmod(row[0], row[1])
        if args['skip_mtime'] is False:
            os.utime(row[0], (row[2], row[2]))
        if len(row)>3:
            uid = -1
            gid = -1
            if args['skip_user'] is False:
                if isinstance(row[3], int):
                    uid = row[3]
                else:
                    uid = pwd.getpwnam(row[3]).pw_uid
            if args['skip_group'] is False:
                if isinstance(row[4], int):
                    gid = row[4]
                else:
                    gid = grp.getgrnam(row[4]).gr_gid
            os.chown(row[0], uid, gid)

def parse_cmd_line():
    """Parse command line arguments"""
    args = argparse.ArgumentParser(description="Command line parser")

    args.add_argument('--data', help='Path to database', metavar='PATH',
                      default='.metadata')
    args.add_argument('-f', '--force', help='Force to commit',
                      default=False, action='store_true')
    args.add_argument('-O', '--owner', help='Add symbolic owner',
                      default=False, action='store_true')
    args.add_argument('-o', '--numeric-owner', help='Add numeric owner',
                      default=False, action='store_true')
    args.add_argument('-a', '--add-to-git', help='Commit database to git',
                      default=False, action='store_true')
    args.add_argument('-U', '--skip-user', help='Skip user during restore',
                      default=False, action='store_true')
    args.add_argument('-G', '--skip-group', help='Skip group during restore',
                      default=False, action='store_true')
    args.add_argument('-P', '--skip-perms', help='Skip perms during restore',
                      default=False, action='store_true')
    args.add_argument('-M', '--skip-mtime', help='Skip mtime during restore',
                      default=False, action='store_true')

    sp_cmd = args.add_subparsers(help='Command', dest='cmd')

    sp_cmd.add_parser('init', help='Setup hooks in .git directory')
    sp_cmd.add_parser('get', help='Store metadata')
    sp_cmd.add_parser('set', help='Restore metadata')
    sp_cmd.add_parser('dump', help='Dump metadata')

    return args.parse_args().__dict__

def __init__():
    args = parse_cmd_line()
    if args['cmd'] == 'get':
        git_get_files_attributs(args)
    elif args['cmd'] == 'dump':
        ret = load_metadata(args)
        print json.dumps(ret, indent=2)
    elif args['cmd'] == 'set':
        git_set_file_attributs(args)

if __name__ == "__main__":
    __init__()
