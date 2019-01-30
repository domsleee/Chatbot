#!/usr/bin/env python3
import os
import argparse
import logging
from Bot import Bot

# Uncomment the following lines to enable verbose logging
#logging.basicConfig(level=logging.INFO)

DEBUG = False

def main(args):
    mybot = Bot("mybot", args.inbox_folder, args.yes, args.user)
    mybot.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='"intelligent" bot')
    parser.add_argument('inbox_folder',
                         help='inbox folder containing JSON message data')
    parser.add_argument('--yes', action='store_true',
                        help='yes to all')
    parser.add_argument('--user', '-u',
                        help='user to mimic')
    main(parser.parse_args())
