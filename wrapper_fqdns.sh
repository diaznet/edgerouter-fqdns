#!/bin/bash

# wrapper_fqdns.sh - v0.2.1
# Can be called from CLI or from EdgeOS scheduler. See README.md for more infos.

# Absolute path to this script
SCRIPT=$(readlink -f "$0")
# Absolute path to this script's directory
SCRIPTPATH=$(dirname "$SCRIPT")

# Declaring wrappers variables fromn Vyatta
vop=/opt/vyatta/bin/vyatta-op-cmd-wrapper
vcfg=/opt/vyatta/sbin/vyatta-cfg-cmd-wrapper

IN_DESC=$($vop show configuration commands | grep -i "^set firewall group address-group FQDN-.* description .*$")
IN_ADDR=$($vop show configuration commands | grep -i "^set firewall group address-group FQDN-.* address .*$")

# Load the python code in the wrapper
PYTHON_CODE=$(cat ${SCRIPTPATH}/fqdns.py)

# Run the Python code and capture output. Output will contain EdgeOS configuration lines.
OUTPUT="$(python -c "$PYTHON_CODE" "$IN_DESC" "$IN_ADDR")"

# Run each configuration line in EdgeOS shell.
echo "$OUTPUT" |
{
  # Enter in configuration mode
  $vcfg begin
  while IFS= read -r line ; do logger $line ; $vcfg $line ; done ;
  # Commit then exit
  $vcfg commit
  $vcfg end
}
