# Mooltipy
A [Mooltipass](http://themooltipass.com) Python library and command line
management utilities.

Under heavy development. This could be called beta quality at the moment.


## Installation & usage
You can install or upgrade to the lastest stable release of mooltipy using pip.

```
# Install
$ sudo pip install mooltipy

# Upgrade
$ sudo pip install mooltipy --upgrade
```

### Manage login contexts
Set login contexts with mooltipy:

```
# Add or update user_name at example.com with a randomly generated password.
$ mooltipy login set example.com -u user_name

# ... some sites only allow alphanumeric passwords; avoid symbols in a generated password.
$ mooltipy login set example.com -u user_name -c alnum

# ... ask for the password rather than generating one.
$ mooltipy login set example.com -u user_name -p
```

Get passwords from the Mooltipass. This could be used in a script, for example.

```
$ mysql --user root --password=$(mplogin get mysql)
```

List contexts stored in the Mooltipass:

```
$ mooltipy login list
Context:                                Login(s):
--------                                ---------
Example.com                             user_name
Example.net                             user_name

# Unix shell-style globbing supported
$ mooltipy list *.net
Context:                                Login(s):
--------                                ---------
Example.net                             user_name
```

### Manage data contexts
The Mooltipass can be used to securely store small data files! Think ssh or gpg
keys and cryptocurrency wallets.

```
$ mooltipy data set ssh_key ~/.ssh/id_rsa
$ mooltipy data get ssh_key ./restored_key
```

It supports reading from / writing to stdin / stdout for convenience, but this
can also be used as a workaround to store values greater than 31 characters.

```
$ echo "this-is-a-secure-api-key" | mpdata set example-api-key
$ echo $(mpdata get example-api-key)
this-is-a-secure-api-key
```

**Warning**: Do not disconnect your mooltipass during data transfer! Ctrl-C can
be used to gracefully cancel a transfer.

### Handle favorites
Use the favorites utility to get, set and remove entries in favorite slots.

```
$ mooltipy favorites list
$ mooltipy favorites set
$ mooltipy favorites del
```

### Set parameters
There are some parameters which can be set on the Mooltipass such as the
keyboard layout or enabling offline mode.

```
$ mooltipy parameters set offline_mode 1
$ mooltipy parameters list
Current Mooltipass Parameters
-----------------------------
flash_screen        : True
keyboard_layout     : 0x92
lock_timeout        : 60
lock_timeout_enable : False
offline_mode        : True
screen_saver_speed  : 15
screensaver         : False
touch_charge_time   : 0
touch_di            : 6
touch_prox_os       : 0x73
touch_wheel os_0    : 0x21
touch_wheel os_1    : 0x21
touch_wheel os_2    : 0x21
tutorial            : False
user_intr_timer     : 15
user_req_cancel     : False
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

if mooltipass is None:
    print('Could not connect to the Mooltipass')
    sys.exit(0)

mootipass.do_some_stuff()
```

We'll document more soon, for now check out the MooltipassClient and
Mooltipass classes to see what's implemented and see each utility as excellent
examples of how to interact with the device.

## Support
Problems, questions, comments, feature requests? We're available in the
[Mooltipass subreddit](http://reddit.com/r/mooltipass) and idle on freenode
as vic or codegor* in #mooltipass. E-mailing mooltipy [at my domain] 
oSquat.com will reach me very quickly too.
