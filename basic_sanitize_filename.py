# assumption: Remediate just filenames, not path to filenames
# input: absolute path to directory containing filename to remediate

import sys
import os

# get arguments. Returns a list, first entry is name of script
# assuming called as follows: python3 basic_sanitize_filename.py hi
# rest of arguments should be absolute paths to directories
args = sys.argv
print(args)
args.pop(0)
print(args)

def process_file(target_file):
    # separate file into basename and extension
    basename, extension = os.path.splitext(target_file)
    print(basename)
    print(extension)

def process_dir(target_dir):
    for root, subdirs, files in os.walk(target_dir):
        for target_file in files:
            print(os.path.join(root,target_file))
            process_file(target_file)

# for each argument
for arg in args:
    # only process arg if it's an absolute path and
    # arg is a dir
    if ( os.path.isabs(arg) and os.path.isdir(arg) ):
        print(arg)
        process_dir(arg)
    else:
        print("Kaboom!")

