#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    fqdns.py - v0.2

        usage: fqdns.py [-h] [--prefix PREFIX] in-desc in-addr

        Convert FQDNs to IP

        positional arguments:
        in-desc          Input descriptions
        in-addr          Input addresses

        optional arguments:
        -h, --help       show this help message and exit
        --prefix PREFIX  Prefix for Address Group descriptions
        --debug          Enable DEBUG messages
        ubnt@edgeos $ 

    Can be ran independentely in the cli or via the wrapper.
    Example from CLI:

    $ python fqdns.py --prefix "FQDN-" --debug \
        " \
        set firewall group address-group FQDN-0.fr.pool.ntp.org description FQDN-0.fr.pool.ntp.org \
        set firewall group address-group FQDN-1.fr.pool.ntp.org description FQDN-1.fr.pool.ntp.org \
        set firewall group address-group FQDN-2.fr.pool.ntp.org description FQDN-2.fr.pool.ntp.org \
        " \
        " \
        set firewall group address-group FQDN-0.fr.pool.ntp.org address 5.196.28.76 \
        set firewall group address-group FQDN-0.fr.pool.ntp.org address 94.231.206.1 \
        set firewall group address-group FQDN-0.fr.pool.ntp.org address 82.64.45.50 \
        set firewall group address-group FQDN-0.fr.pool.ntp.org address 80.74.64.2 \
        set firewall group address-group FQDN-1.fr.pool.ntp.org address 162.159.200.123 \
        set firewall group address-group FQDN-1.fr.pool.ntp.org address 92.243.6.5 \
        set firewall group address-group FQDN-1.fr.pool.ntp.org address 195.154.174.209 \
        set firewall group address-group FQDN-1.fr.pool.ntp.org address 82.65.141.217 \
        set firewall group address-group FQDN-1.fr.pool.ntp.org address 146.59.88.209 \
        set firewall group address-group FQDN-2.fr.pool.ntp.org address 162.159.200.1 \
        set firewall group address-group FQDN-2.fr.pool.ntp.org address 109.24.224.121 \
        set firewall group address-group FQDN-2.fr.pool.ntp.org address 194.57.169.1 \
        set firewall group address-group FQDN-2.fr.pool.ntp.org address 51.255.197.148 \
        set firewall group address-group FQDN-3.fr.pool.ntp.org address 51.178.43.227 \
        set firewall group address-group FQDN-3.fr.pool.ntp.org address 95.81.173.155 \
        set firewall group address-group FQDN-3.fr.pool.ntp.org address 82.64.32.33 \
        "

    See README.md for installation instructions.
"""

import sys
import socket
import argparse
import logging

def get_hostnames(fqdn):
    logging.debug('get_hostnames(fqdn = \'%s\')' % fqdn)

    try:
        # Return a list of IP addresses
        ip_list = socket.gethostbyname_ex(fqdn)[2]
        return ip_list
    except Exception as e:
        # Could not resolve for whatever reason, return an empty list
        logging.error('Exception while resolving %s. Skipping...' % fqdn)
        return []

# Parsing options in the command line
parser = argparse.ArgumentParser(description='Convert FQDNs to IP')
parser.add_argument('in_desc', metavar='in-desc', help='Input descriptions')
parser.add_argument('in_addr', metavar='in-addr', help='Input addresses')
parser.add_argument('--prefix', help='Prefix for Address Group descriptions')
parser.add_argument('--debug', help='Enable DEBUG messages', action='store_true')
args = parser.parse_args()

if (args.debug):
    level = logging.DEBUG
else:
    level = logging.INFO

# Configure the logger
logging.basicConfig(
    format = '%(asctime)s - %(levelname)s \t %(message)s',
    level = level
    )

if (args.prefix):
    prefix = args.prefix
else:
    prefix = "FQDN-"
logging.debug('Set prefix to %s.' % prefix)

# Ingurgitate the description and address lines, remove all leading and trailing whitespaces.
desc_commands = args.in_desc.strip()
addr_commands = args.in_addr.strip()

# We're missing the newlines, adding them back, then split into a list of lines
lstLinesDesc = desc_commands.replace(" set", "\nset").split("\n")
lstLinesAddr = addr_commands.replace(" set", "\nset").split("\n")

logging.debug('Loaded descriptions: ')
for dbg_line in lstLinesDesc:
    logging.debug('\t %s' % dbg_line)
logging.debug('Loaded addresses: ')
for dbg_line in lstLinesAddr:
    logging.debug('\t %s' % dbg_line)

# in EdgeOS syntax to add an address-group object:
# set firewall group address-group <group_name> description <txt_description>
# set firewall group address-group <group_name> address     <txt_description>
# [0] [   1  ] [ 2 ] [     3     ] [     4    ] [    5    ] [       6       ]
# <group_name> is at the 4th position, limited to 31 chars
# <txt_description> and txt_address are at the 6th position
pos_group_name = 4
pos_txt_description = 6
pos_txt_address = 6

outCmd = []
outDelCmd = []

# Loop through the list of description lines
for idx,line in enumerate(lstLinesDesc, start=0):
    # Break each word separated by a space into a list, put it back in the same list
    lstLinesDesc[idx] = line.split()
for idx,line in enumerate(lstLinesAddr, start=0):
    # Break each word separated by a space into a list, put it back in the same list
    lstLinesAddr[idx] = line.split()

###
### First we're going to resolve all our FQDNS
### 
# Loop through the list, through the words
for lstCmdDesc in lstLinesDesc:
    # Description value is at index pos_txt_description, and should start with prefix
    if lstCmdDesc[pos_txt_description].startswith(prefix):
        # Get a list of IP from the hostname, obtained from description value
        for ip in get_hostnames(lstCmdDesc[pos_txt_description][len(prefix):]):
            if ip:
                logging.debug('outCmd += (\'%s\', \'%s\')' % (lstCmdDesc[pos_group_name], ip))
                outCmd.append((lstCmdDesc[pos_group_name], ip))

###
### Then we're going to compare with what's already in the addresses
### 
# Loop through the list, through the words
if not lstLinesAddr == [[]]:
    for lstCmdAddr in lstLinesAddr:
        # Check if we found an IP address
        ip = lstCmdAddr[pos_txt_address]
        group_name = lstCmdAddr[pos_group_name]
        try:
            socket.inet_aton(ip)
            match = False
            # We're trying to find this IP/Firewall Groupe pair in our list. If found, we remove it from the list we will commit.
            # It is not necessary to add it again, as this would produce an error and cost time.
            for cmdLine in outCmd:
                if cmdLine[1] == ip and cmdLine[0] == group_name:
                    match = True
                    logging.debug('outCmd -= (\'%s\', \'%s\')' % (cmdLine[0], cmdLine[1]))
                    outCmd.remove((cmdLine[0],cmdLine[1]))
            # Didn't find this IP anywhere in the new list, we will have to remove it.
            if match == False:
                logging.debug('outDelCmd += (\'%s\', \'%s\')' % (lstCmdAddr[pos_group_name], ip))
                outDelCmd.append((lstCmdAddr[pos_group_name], ip))
        except socket.error:
            pass

# Finally, print the lines to add new IP addresses
logging.info('About to ADD %d lines...' % len(outCmd))
for cmdLine in outCmd:
    line = "set firewall group address-group %s address %s" % (cmdLine[0], cmdLine[1])
    logging.debug(line)
    print(line)

# Finally, print the lines to delete old/no lomger valid IP addresses
logging.info('About to DELETE %d lines...' % len(outDelCmd))
for cmdDelLine in outDelCmd:
    line = "delete firewall group address-group %s address %s" % (cmdDelLine[0], cmdDelLine[1])
    logging.debug(line)
    print(line)