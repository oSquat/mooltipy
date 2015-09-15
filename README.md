# Mooltipy
A [Mooltipass](http://themooltipass.com) Python library and command line
management utilities.

Under heavy development. This could be called beta quality at the moment.


## Installation & usage
You can install or upgrade to the lastest stable release of mooltipy using pip.
```
# Install
user@box:~/$ sudo pip install mooltipy

# Upgrade
user@box:~/$ sudo pip install mooltipy --upgrade
```

### Manage login contexts
Set login contexts with mooltipy:

```
# Add or update user_name at example.com with a randomly generated password.
$ mooltipy set example.com -u user_name

# ... some sites only allow alphanumeric passwords; avoid symbols in a generated password.
$ mooltipy set example.com -u user_name -c alnum

# ... ask for the password rather than generating one.
$ mooltipy set example.com -u user_name -p
```

Get passwords from the Mooltipass:

```
user@box:~/$ mysql --user root --password=$(mplogin get mysql)
```

List contexts stored in the Mooltipass:

```
user@box:~/$ mplogin list
Context:                                Login(s):
--------                                ---------
Example.com                             user_name
Example.net                             user_name

# Unix shell-style globbing supported
user@box:~/$ mplogin list *.net
Context:                                Login(s):
--------                                ---------
Example.net                             user_name
```

### Manage data contexts
The Mooltipass can be used to securely store small data files! Think ssh or gpg
keys and cryptocurrency wallets.

```
$ mooltipy data import ssh_key ~/.ssh/id_rsa
$ mooltipy data export ssh_key ./restored_key
```

**Warning**: Do not disconnect your mooltipass during data transfer! Ctrl-C can
be used to gracefully cancel a transfer.

### Handle favorites
Use the favorites utility to get, set and remove entries in favorite slots.

```
$ mooltipy favorites get --help
$ mooltipy favorites set --help
$ mooltipy favorites del --help
```

### Mooltipy is a wrapper
The mooltipy command is a wrapper for individual utilities. To get help for any
of the individual utilities you can:
```
$ mooltipy data --help
$ mooltipy login --help
$ mooltipy favorites --help
```
You can also call any of the utilities directly by prefixing *mp* to the name
of the utility:
```
$ mpdata --help
$ mplogin --help
$ mpfavorites --help
```

### Using the Mooltipass module
To utilize the MooltipassClient class:
```python
from mooltipy import MooltipassClient
import sys

mooltipass = MooltipassClient()

if mooltipass.ping():
    print('Connected to the mooltipass!')
else:
    print('Failed to connect to mooltipass.')
    sys.exit(0)

mootipass.do_some_stuff()
```

We'll document more soon, for now check out the MooltipassClient and
Mooltipass classes to see what's implemented and see each utility as an
example of how to interact with the device.

### Support
Problems, questions, comments, feature requests, flames? I'm
[mooltigeek](http://reddit.com/u/mooltigeek) on the
[Mooltipass subreddit](http://reddit.com/r/mooltipass) and I idle on freenode
as modest in #mooltipass. E-mailing mooltipy [at my domain] oSquat.com will reach
me very quickly too.
