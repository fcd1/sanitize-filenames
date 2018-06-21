#!/usr/bin/env python2

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage MCPClient
# @author Joseph Perry <joseph@artefactual.com>

from __future__ import print_function
import string
import os
from shutil import move as rename
import sys
import unicodedata
from unidecode import unidecode
# from archivematicaFunctions import unicodeToStr
import argparse
import logging
from datetime import datetime
import csv
# Note: in python 3.x, ConfigParser has been renamed configparser
import ConfigParser
import getpass

# VERSION = "1.10." + "$Id$".split(" ")[1]
# fcd1, 12Jun18: Current requirements: remove all periods except last, remove parens
valid = "-_.()" + string.ascii_letters + string.digits
replacementChar = "_"
# come up with a better name for the var below. Basically, I want all logs, besides being created
# where specified at (if specified) the command line, to also be duplicated in a centralized location
# for debugging by development staff
centralizedLoggingDir=os.getcwd()

def unicodeToStr(string):
    if isinstance(string, unicode):
        string = string.encode("utf-8")
    return string

def transliterate(basename):
    # We get a more meaningful name sanitization if UTF-8 names
    # are correctly decoded to unistrings instead of str
    try:
        return unidecode(basename.decode('utf-8'))
    except UnicodeDecodeError:
        return unidecode(basename)


def sanitizeName(basename):
    ret = ""
    basename = transliterate(basename)
    for c in basename:
        if c in valid:
            ret += c
        else:
            ret += replacementChar
    return ret.encode('utf-8')


def sanitizePath(path):
    basename = os.path.basename(path)
    dirname = os.path.dirname(path)
    sanitizedName = sanitizeName(basename)

    if basename == sanitizedName:
        return path
    else:
        n = 1
        fileTitle, fileExtension = os.path.splitext(sanitizedName)
        sanitizedName = os.path.join(dirname, fileTitle + fileExtension)

        while os.path.exists(sanitizedName):
            sanitizedName = os.path.join(dirname, fileTitle + replacementChar + str(n) + fileExtension)
            n += 1
        rename(path, sanitizedName)
        return sanitizedName


def sanitizeRecursively(path):
    path = os.path.abspath(path)
    sanitizations = {}

    sanitizedName = sanitizePath(path)
    if sanitizedName != path:
        path_key = unicodeToStr(
            unicodedata.normalize('NFC', path.decode('utf8')))
        sanitizations[path_key] = sanitizedName
    if os.path.isdir(sanitizedName):
        for f in os.listdir(sanitizedName):
            sanitizations.update(sanitizeRecursively(os.path.join(sanitizedName, f)))

    return sanitizations

# Probably do not want to use a default for the local logfile, since it is quite
# probable that this script will run directly in the directory where the files are,
# and we don't want to create a logfile there. Plus, we have the centralized
# duplicate one.
def setupLogging(systemLogfile,localLogfile=datetime.now().strftime("%d%b%y_%H%M%S")):

    logger = logging.getLogger('sanitize_filenames_logger')
    logger.setLevel('INFO')

    # Setup system-wide logging handler here. All executions of this script will
    # log to this file (in addition to local logging), this facilitating
    # after-the-fact debugging irregardless of who ran the script
    # The above assumes USG is OK with a group write permission, which
    # would be equivalent to the group that has rename privs on the asset files.
    systemLogfileHandler = logging.FileHandler(systemLogfile)
    logger.addHandler(systemLogfileHandler)

    # local file for logging
    localLogfileHandler = logging.FileHandler(localLogfile)
    logger.addHandler(localLogfileHandler)

    # tty. Believe stderr
    streamHandler = logging.StreamHandler()
    logger.addHandler(streamHandler)

    # log info about user, script location, etc.
    logger.info(80 * '#')
    logger.info('Logging started on ' + datetime.now().strftime("%x") + ' at ' + datetime.now().strftime("%X"))
    logger.info('User running script: os.getlogin()) returns ' + os.getlogin() + ', getpass.getuser() returns ' + getpass.getuser() + '.')
    logger.info('Location of this script: ' + os.path.abspath(__file__))

    return logger

def finalLoggingInfo(logger):
    logger.info('Logging stopped on ' + datetime.now().strftime("%x") + ' at ' + datetime.now().strftime("%X"))
    logger.info(80 * '#')

def readConfigSettings():
    systemConfig = ConfigParser.ConfigParser()
    userConfig = ConfigParser.ConfigParser()
    systemConfig.read('tmp/systemConfigs.cfg')
    userConfig.read('tmp/userConfigs.cfg')
    print()
    print(systemConfig.get('DEFAULT','systemLogFile'))
    print()
    return (systemConfig, userConfig)

def writeCsvFile(csvfilename,iterable):
    headerfields = ['full_path_original_filename','full_path_sanitized_name']
    with open('test.csv','w') as csvfile:
        csvDictWriter = csv.DictWriter(csvfile,headerfields)
        csvDictWriter.writerow({'full_path_original_filename' : "I'm an original filename",
                        'full_path_sanitized_name' : "I_m_the_sanitized_filename"})
    with open('test2.csv','w') as csvfile:
        csvWriter = csv.writer(csvfile, headerfields)
        csvWriter.writerows([['orig','sanit'],
                             ['orig2','sanit2']])

if __name__ == '__main__':

    # fcd1, 19Jun18: Read in the configs:
    systemConfigSettings, userConfigSettings = readConfigSettings()
    print(systemConfigSettings.get('DEFAULT','systemLogFile'))

    logger = setupLogging(systemLogfile=systemConfigSettings.get('DEFAULT','systemLogFile'),
                 localLogfile='tmp/localLogfile.log')

    logger.info('About to start processing')

    finalLoggingInfo(logger)
    parser = argparse.ArgumentParser(description='Sanitize filenames.')
    parser.add_argument('-o','--output-csv-file', help='Specifies CSV output file')
    parser.add_argument('-l','--logfile', help='Specifies logfile, default is sanitize.log')
    parser.add_argument('paths',nargs='+')
    args = parser.parse_args()
    for path in args.paths:
        print(path)
        if not os.path.isdir(path):
            print("Not a directory: " + path, file=sys.stderr)
    writeCsvFile('testfile','testiterable')
    finalLoggingInfo(logger)
    
if __name__ == '__originalmain__':
    parser = argparse.ArgumentParser(description='Sanitize filenames.')
    path = sys.argv[1]
    if not os.path.isdir(path):
        print("Not a directory: " + path, file=sys.stderr)
        sys.exit(-1)
    print("Scanning: ", path)
    sanitizations = sanitizeRecursively(path)
    for oldfile, newfile in sanitizations.items():
        print(oldfile, " -> ", newfile)
    print("TEST DEBUG CLEAR DON'T INCLUDE IN RELEASE", file=sys.stderr)
    print("Printing out sanitizations:")
    print(sanitizations)
    print("Printing out sanitizations.items():")
    print(sanitizations.items())
