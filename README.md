# Update Linux IP sets from blocklist

This is a simple tool that knows how to read a list of IPs (v4 and v6) from
[blocklist.de](https://www.blocklist.de/) and stick them into Linux kernel
IP sets.  They can then be used in iptables/ip6tables/nftables firewall rules.

# Requirements

On Debian-derived Linux distributions:

```
apt install python3-requests-cache python3-pyroute2 sqlite3
```

Or more generally:
```
pip3 install pyroute2 requests-cache
```

# Command line parameters

Usage: `update-ipset-from-blocklist.py <ipset-name> <FROM|TO> <blocklist-url>`

All of the parameters are optional.  Here's what they mean:

* ipset-name: This is the base name for the ipset tables which will be created
              and populated.  Two ipsets will be created using this basename.
              One ipset will be created named `$NAME.ipv4`,
              and the other will be named `$NAME.ipv6`.  For example, a name of
              `blocklist.de` would result in ipsets named `blocklist.de.ipv4`
              and `blocklist.de.ipv6`.
* FROM|TO: Entries in an ipset can match the source or target address.  This
           chooses which.  The default is `FROM`, which is suitable for use in
           an iptables INPUT chain.
* blocklist-url: A URL pointing to a text file with some IP addresses to block,
                 separated by whitespace. The default is
                 https://lists.blocklist.de/lists/all.txt.

# Installation

Stick it in /usr/local/bin/ or somewhere.  Call it periodically from a cron
script.

Add some iptables/ip6tables rules which check it.  Like this:

```
iptables  -A INPUT -m set --match-set blocklist.de.ipv4 src -j DROP
ip6tables -A INPUT -m set --match-set blocklist.de.ipv6 src -j DROP
```

Set things up with the `iptables-persistent` package, or the `iptables-save`
command or somesuch so that the rules persist across a reboot.  Your distro
probably has some docs on that, here's [Debian's](https://wiki.debian.org/iptables#Making_Changes_permanent).

Have fun.  And maybe try not to get your DNS server or the blocklist's web
server listed... otherwise the list won't automatically update any more.

# Customization

Apart from the command line parameters listed above, there are a couple of
hard-coded parameters in here.  If you want to make them easier to customize,
patches are welcome.  Here's the stuff I can think of:

* The HTTP client object is configured with persistent caching enabled.  It will
  store previous responses in a sqlite database, called
  `/tmp/blocklist_cache.sqlite3`, and will reuse that data for the following 4
  hours.  If you don't care about caching, you could make it a `requests` session
  object and lose the `requests_cached` dependency.
* If the IP sets don't already exist in the kernel, they are created as `hash:ip`
  tables.  Other types of tables exist, see [the ipset manpage, `SET TYPES`
  section](https://ipset.netfilter.org/ipset.man.html#lbAS) for more details.
  At time of writing, the available options are bitmaps, hashes, or lists.
