#!/bin/bash
# Declaring wrappers variables fromn Vyatta
vop=/opt/vyatta/bin/vyatta-op-cmd-wrapper
vcfg=/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper

IN_DESC=$($vop show configuration commands | grep -i "^set firewall group address-group FQDN-.* description .*$")
IN_ADDR=$($vop show configuration commands | grep -i "^set firewall group address-group FQDN-.* address .*$")

# Python Code Begins here

PYTHON_CODE=$(cat <<END
import sys
import socket
import argparse

def get_hostnames(fqdn):
    try:
        # Return a list of IP addresses
        return socket.gethostbyname_ex(fqdn)[2]
    except Exception as e:
        # Could not resolve for whatever reason, return an empty list
        return []

# Parsing options in the command line
parser = argparse.ArgumentParser(description='Convert FQDNs to IP')
parser.add_argument('in_desc', metavar='in-desc', help='Input descriptions')
parser.add_argument('in_addr', metavar='in-addr', help='Input addresses')
parser.add_argument('--prefix', help='Prefix')
args = parser.parse_args()

if (args.prefix):
    prefix = args.prefix
else:
    prefix = "FQDN-"
desc_commands = args.in_desc
addr_commands = args.in_addr

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

# We're missing the newlines, adding them back, then split into a list of lines
lstLinesDesc = desc_commands.replace(" set", "\nset").split("\n")
lstLinesAddr = addr_commands.replace(" set", "\nset").split("\n")


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
        # Get a list of IP from the hostname, obtained from description value, we removed
        for ip in get_hostnames(lstCmdDesc[pos_txt_description][len(prefix):]):
            if ip:
                outCmd.append([lstCmdDesc[pos_group_name], ip])

###
### Then we're going to compare with what's already in the addresses
### 
# Loop through the list, through the words
if not lstLinesAddr == [[]]:
    for lstCmdAddr in lstLinesAddr:
        # Check if we found an IP address
        ip = lstCmdAddr[pos_txt_address]
        try:
            socket.inet_aton(ip)
            match = False
            # We're trying to find this IP in our list. If found, we remove it from the list we will commit.
            # Itz is not necessary to add it again, as this would produce an error and cost time.
            for cmdLine in outCmd:
                if cmdLine[1] == ip:
                    match = True
                    outCmd.remove([cmdLine[0],cmdLine[1]])
            # Didn't find this IP anywhere in the new list, we will have to remove it.
            if match == False:
                outDelCmd.append([lstCmdAddr[pos_group_name], ip])
        except socket.error:
            pass
for cmdLine in outCmd:
    print "set firewall group address-group %s address %s" % (cmdLine[0], cmdLine[1])
for cmdDelLine in outDelCmd:
    print "delete firewall group address-group %s address %s" % (cmdDelLine[0], cmdDelLine[1])
END
)

# Python Code ends here

# Run the Python code and capture output. Output will contain EdgeOS configuration lines.
OUTPUT="$(python -c "$PYTHON_CODE" "$IN_DESC" "$IN_ADDR")"

# Run each configuration line in EdgeOS shell.
echo "$OUTPUT" |
{
  $vcfg begin
  while IFS= read -r line ; do logger $line ; $vcfg $line ; done ;
  $vcfg commit
  $vcfg end
}
