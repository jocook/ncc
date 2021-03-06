#!/usr/bin/env python
import sys
from argparse import ArgumentParser
from ncclient import manager
from lxml import etree
from BeautifulSoup import BeautifulSoup
import logging
import time
import datetime


def get(m, filter=None, xpath=None):
    if filter and len(filter) > 0:
        return m.get(filter=('subtree', filter))
    elif xpath and len(xpath)>0:
        return m.get(filter=('xpath', xpath))
    else:
        print ("Need a filter for oper get!")
        return None
        
        
if __name__ == '__main__':

    parser = ArgumentParser(description='Select your siple poller parameters:')

    # Input parameters
    parser.add_argument('--host', type=str, required=True,
                        help="The device IP or DN")
    parser.add_argument('-u', '--username', type=str, default='cisco',
                        help="Go on, guess!")
    parser.add_argument('-p', '--password', type=str, default='cisco',
                        help="Yep, this one too! ;-)")
    parser.add_argument('--port', type=int, default=830,
                        help="Specify this if you want a non-default port")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Do I really need to explain?")

    # other options
    parser.add_argument('--cadence', type=int, default=5,
                        help="Cadence of gets")
    parser.add_argument('--display-tags', type=str, nargs='+',
                        help="A list of display XML tags; first value matching displayed")

    # Only one type of filter
    g = parser.add_mutually_exclusive_group()
    g.add_argument('-s', '--subtree', type=str,
                   help="XML-formatted netconf subtree filter")
    g.add_argument('-x', '--xpath', type=str,
                   help="XPath-formatted filter")

    # Basic operations
    g = parser.add_mutually_exclusive_group()
    g.add_argument('--get-oper', action='store_true',
                   help="Get oper data")
    
    args = parser.parse_args()

    if args.verbose:
        handler = logging.StreamHandler()
        for l in ['ncclient.transport.ssh', 'ncclient.transport.session', 'ncclient.operations.rpc']:
            logger = logging.getLogger(l)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)

    #
    # Could use this extra param instead of the last four arguments
    # specified below:
    #
    # device_params={'name': 'iosxr'}
    #
    def unknown_host_cb(host, fingerprint):
        return True
    m =  manager.connect(host=args.host,
                         port=args.port,
                         username=args.username,
                         password=args.password,
                         allow_agent=False,
                         look_for_keys=False,
                         hostkey_verify=False,
                         unknown_host_cb=unknown_host_cb)

    # if args.get_oper:
    #     if args.xpath:
    #         while True:
    #             get(m, xpath=args.xpath)
    #             time.sleep(args.cadence)
    #     elif args.subtree:
    #         get(m, filter=args.subtree)
    #     else:
    #         print("Need to have a filter!")
    #         sys.exit(1)
    kw = {}
    if args.xpath:
        kw['xpath'] = args.xpath
    elif args.subtree:
        kw['filter'] = args.subtree
    while True:
        st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        result = get(m, **kw)
        if not args.display_tags:
            print(st)
            print etree.tostring(etree.fromstring(result.data_xml), pretty_print=True)
        else:
            values = []
            for p in args.display_tags:
                try:
                    p_val = BeautifulSoup(
                        result.xml,
                        convertEntities=BeautifulSoup.HTML_ENTITIES).find(p).getText()
                    values.append(p+"="+p_val)
                except AttributeError as e:
                    values.append(p+"=<not_found>")
            print("{}: {}".format(st, ", ".join(values)))
        time.sleep(args.cadence)
