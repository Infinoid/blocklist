#!/usr/bin/env python3

import json
from pyroute2.ipset import IPSet, PortRange, PortEntry, _IPSetError
from pyroute2.netlink import nla_slot
import re
import requests_cache
from socket import AddressFamily
import sys

if len(sys.argv) < 2:
    raise Exception("Usage: {} <ipset-name> [FROM|TO [<blocklist-url>]]".format(sys.argv[0]))

ipset_name = sys.argv[1]
ipset_name_ipv4 = ipset_name + ".ipv4"
ipset_name_ipv6 = ipset_name + ".ipv6"

from_to = "FROM"
if len(sys.argv) > 2:
    from_to = sys.argv[2]
if from_to not in ['FROM', 'TO']:
    raise Exception("FROM_TO argument must be 'FROM' or 'TO'")
from_to_attr = 'IPSET_ATTR_IP_{}'.format(from_to)

blocklist_url = "https://lists.blocklist.de/lists/all.txt"
if len(sys.argv) > 3:
    blocklist_url = sys.argv[3]

api = IPSet()

api.create(ipset_name_ipv4, stype="hash:ip", family=AddressFamily.AF_INET , exclusive=False)
api.create(ipset_name_ipv6, stype="hash:ip", family=AddressFamily.AF_INET6, exclusive=False)

ipv4_ipsets = api.list(ipset_name_ipv4)
ipv6_ipsets = api.list(ipset_name_ipv6)
# parse current addresses
ipset_addresses = set()

def parse_ipset_addrs(ipsets, addrtype, outset):
    for ipset in ipsets:
        adt = ipset.get_attr('IPSET_ATTR_ADT')
        ipaddr_attr = 'IPSET_ATTR_IPADDR_{}'.format(addrtype)
        for record in adt.get_attrs('IPSET_ATTR_DATA'):
            for record in record.get_attrs(from_to_attr):
                for record in record.get_attrs(ipaddr_attr):
                    outset.add(record)

parse_ipset_addrs(ipv4_ipsets, "IPV4", ipset_addresses)
parse_ipset_addrs(ipv6_ipsets, "IPV6", ipset_addresses)

# fetch blocklist data
webclient = requests_cache.CachedSession(
    "/tmp/blocklist_cache",
    backend="sqlite",
    expire_after=3600*4,
    match_headers=True,
)

response = webclient.get(blocklist_url)
data = response.text

blocklist_addresses = set(data.split())
count_additions = 0
count_removals = 0

# apply new additions
for addr_to_add in blocklist_addresses.difference(ipset_addresses):
    if ":" in addr_to_add:
        # ipv6 address
        api.add(ipset_name_ipv6, addr_to_add, family=AddressFamily.AF_INET6, etype="ip")
    else:
        # ipv4 address
        api.add(ipset_name_ipv4, addr_to_add, family=AddressFamily.AF_INET, etype="ip")
    count_additions += 1

# apply new removals
for addr_to_remove in ipset_addresses.difference(blocklist_addresses):
    if ":" in addr_to_remove:
        # ipv6 address
        api.delete(ipset_name_ipv6, addr_to_remove, family=AddressFamily.AF_INET6, etype="ip")
    else:
        # ipv4 address
        api.delete(ipset_name_ipv4, addr_to_remove, family=AddressFamily.AF_INET, etype="ip")
    count_removals += 1

if count_additions > 0:
    print("Added {} new addresses.".format(count_additions))
if count_removals > 0:
    print("Removed {} dead addresses.".format(count_removals))
