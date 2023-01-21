#!/usr/bin/env python3

# periodical one-way directory synchronization
# author: Damián Sova
# date: 27.12.2022

import sys
import argparse
import os
import shutil
import time
import hashlib
import logging

def do_every(period, function, *args):
    """Method that executes function with arguments every period."""

    def g_tick():
        """Period generator."""

        t = time.time()
        while True:
            t += period
            yield max(t - time.time(), 0)
    g = g_tick()

    while True:
        time.sleep(next(g))
        function(*args)

def sync_directory(source, destination):
    """Recursively synchronize the source directory to the destination directory."""

    source = source if source[-1] == '/' else source + '/'
    destination = destination if destination[-1] == '/' else destination + '/'

    if not os.path.exists(destination):
        # completely copy all files from source to destination
        logging.info(f"Copied {len(os.listdir(source))} files from '{source}' to '{destination}'")
        shutil.copytree(source, destination)
        return

    src_files = sorted(os.listdir(source))
    dst_files = os.listdir(destination)

    # Remove files from destination directory if they are not in source directory
    for file in dst_files:
        dst_file = destination + file
        if file not in src_files:
            shutil.rmtree(dst_file) if os.path.isdir(dst_file) else os.remove(dst_file)
            logging.info(f"Removed: '{file}' from '{destination}'")
    
    # Copy files if missing in the destination directory or changed in source directory
    for file in src_files:
        src = source + file
        dst = destination + file

        # This is the case when our file in destination doesn't exist
        if file not in dst_files:
            shutil.copytree(src, dst) if os.path.isdir(src) else shutil.copy(src, dst)
            logging.info(f"Copied: '{file}' to '{dst}'")
            continue

        # This is the case when we process a directory -> recursively sync the directory
        if os.path.isdir(src):
            sync_directory(src, dst)

        # This is the case when we process a file
        else:
            src_hash = hashlib.sha1()
            with open(src, 'rb') as f:
                src_string = f.read()
                src_hash.update(src_string)
            
            dst_hash = hashlib.sha1()
            with open(dst, 'rb') as f:
                dst_string = f.read()
                dst_hash.update(dst_string)

            if src_hash.hexdigest() != dst_hash.hexdigest():
                # The content of the files is not same
                shutil.copytree(src, dst) if os.path.isdir(src) else shutil.copy(src, dst)
                logging.info(f"Copied: '{file}' to '{dst}'")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="path to the source directory to be synchronized")
    parser.add_argument("destination", help="path to the destination directory of synchronization")
    parser.add_argument("interval", help="synchronization interval in seconds", type=int)
    parser.add_argument("logs", help="path to the logs destination")
    args = parser.parse_args()

    try:
        for directory in [args.source, args.destination, args.logs]:
            if not os.path.exists(directory):
                os.makedirs(directory)

        logging.basicConfig(
            filename = (args.logs if args.logs[-1] == '/' else args.logs + '/') + "synchronization.log",
            level = logging.INFO,
            format='[ %(asctime)s ][ %(levelname)s ] - %(message)s',
            datefmt='%m.%d.%Y %I:%M:%S'
        )

        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

        logging.info(f"New synchronization session started!")

        # Periodically sync files from source to destination directory
        do_every(args.interval, sync_directory, args.source, args.destination)
    except Exception as e:
        print(f'Following error occured: {e}')