# Mooltipy

[![License](https://img.shields.io/badge/license-GPLv3%2B-blue.svg)](http://www.gnu.org/licenses/gpl.html)

A [Mooltipass](http://themooltipass.com) Python library and command line
management utilities.


## Installation & usage
Download this latest repository from Github.
```
$ wget https://github.com/oSquat/mooltipy/archive/refs/heads/master.zip
$ unzip ./master.zip
$ sudo python3 ./mooltipy-master/setup.py install
```

### Manage login contexts
Set, get, list and delete login contexts (login credentials) with mooltipy.

Below is an example of how to add new login contexts.

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

Delete a login or entire context.

```
# Delete example_user from example.com
$ mooltipy login del example.com -u example_user

# Erase example.com entirely.
$ mooltipy login del example.com
```

List contexts stored in the Mooltipass.

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
$ mooltipy data del ssh_key
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
Parameter           : init : current
--------------------------------------
after_login         : 0x2b : 0x2b
after_login_enable  : 1    : True
after_pass          : 0x28 : 0x28
after_pass_enable   : 1    : True
flash_screen        : 1    : True
hash_display_enable : 1    : True
invert_screen       : 0    : False
key_delay           : 5    : 5
key_delay_enable    : 1    : False
keyboard_layout     : 0x92 : 0x92
knock_enable        : 1    : True
knock_threshold     : 8    : 8
led_anim_mask       : 0xff : 0xff
lock_enable         : 1    : True
lock_timeout        : 60   : 60
lock_timeout_enable : 0    : False
lut_boot            : 1    : True
offline_mode        : 0    : False
oled_contrast       : 0x80 : 0x80
random_init_pin     : 0    : False
screen_saver_speed  : 15   : 15
screensaver         : 0    : False
touch_charge_time   : 0    : 0
touch_di            : 6    : 6
touch_prox_os       : 0x73 : 0x73
touch_wheel os_0    : 0x21 : 0x21
touch_wheel os_1    : 0x21 : 0x21
touch_wheel os_2    : 0x21 : 0x21
tutorial            : 1    : False
user_intr_timer     : 15   : 15
```

### Mooltipy is a wrapper
The mooltipy command is a wrapper for individual utilities. To get help for any
of the individual utilities you can:

```
$ mooltipy data --help
$ mooltipy login --help
$ mooltipy favorites --help
$ mooltipy parameters --help
```

You can also call any of the utilities directly by prefixing *mp* to the name
of the utility:

```
$ mpdata --help
$ mplogin --help
$ mpfavorites --help
$ mpparams --help
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

Check out the MooltipassClient and Mooltipass classes to see what's implemented
and see each utility as excellent examples of how to interact with the device.
