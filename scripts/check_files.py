#!/usr/bin/env python3
# Check for failed root files based on job log

import glob
import argparse
import os

from tqdm import tqdm
from termcolor import colored

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help = 'Directory containing root files and log files')
    args = parser.parse_args()
    
    path = args.dir
    
    success_string = "Successfully completed."
    
    print(f"Target directory is {path}")
    if not os.path.exists(path):
        raise Exception(f"{path} not valid")
    
    logfiles = glob.glob(os.path.join(path, '*.log'))
    rootfiles = glob.glob(os.path.join(path, '*.root'))
    
    print(f"{len(logfiles)} log files")
    print(f"{len(rootfiles)} root files")
    if len(logfiles) != len(rootfiles):
        print(colored("File number does not match!", "red"))

    print("Checking log files...")
    failed = []
    for f in tqdm(logfiles):
        text  =  open(f, "r").read()
        if text.find(success_string) == -1:
            failed += [f]
    print(f"{len(failed)} failed jobs")

