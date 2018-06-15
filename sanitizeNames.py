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

# VERSION = "1.10." + "$Id$".split(" ")[1]
# fcd1, 12Jun18: Current requirements: remove all periods except last, remove parens
valid = "-_.()" + string.ascii_letters + string.digits
replacementChar = "_"
# come up with a better name for the var below. Basically, I want all logs, besides being created
# where specified at (if specified) the command line, to also be duplicated in a centralized location
# for debugging by development staff
centralizedLoggingDir=os.getcwd()

def yieldNextFile(file_list):
    i = 0
    while (True):
        print(file_list)
        yield i
        i+=1

def generateTestFiles():
    first_set_of_files = map(lambda x : 'batch_one_file' + str(x), range(10))
    pass
    print(first_set_of_files)
    first_set_of_files_bis = map(lambda x,y : 'batch_one_file' + str(x)+ '_' + str(y) , range(10), range(10,20))
    pass
    print(first_set_of_files_bis)
    second_set_of_files = ['batch_two_file' + str(x) for x in range(10)]
    print(second_set_of_files)
    third_set_of_files = ['batch_three_file' + str(x) for x in range(10) if x % 2 == 0]
    print(third_set_of_files)
    fourth_set_of_files = ['file_' + str(x) + '_' + str(y) for x in [1,2,3] for y in [4,5,6] ]
    print(fourth_set_of_files)
    fifth_set_of_files = ['file_' + str(x) + '_' + str(y) for x in [1,2,3] for y in [4,5,6] if x == 2 and y == 6 ]
    print(fifth_set_of_files)

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
def setupLogging(localLogfile=datetime.now().strftime("%d%b%y_%H%M%S")):
    logger = logging.getLogger('fooname')
    localLogfileHandler = logging.FileHandler(localLogfile)
    streamHandler = logging.StreamHandler()
    logger.addHandler(localLogfileHandler)
    logger.addHandler(streamHandler)
    logger.critical('Hi, Fred')
    print(localLogfile)
    print(datetime.now().strftime("%d%b%y_%H%M%S"))

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

if __name__ == '__mainfcd1__':
    # pre testing
    gen = yieldNextFile(['testfile1','testfile2'])
    print(gen.next())
    print(gen.next())
    generateTestFiles()
    # post testing

    # fcd1, 15Jun18: Comment out the setupLogging for now
    # setupLogging()
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
    
if __name__ == '__main__':
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
