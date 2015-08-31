# Mooltipy
A Mooltipass Python library and command line management utilities.

Under heavy development. I just got my unit ~ a couple weeks ago. This could be
called alpha stage work at the moment.

## Installation & Usage
You can install mooltipy using pip.
```
user@box:~/$ pip install mooltipy
```

### Manage Login Contexts
Manage login contexts with Mooltipy. The example below is a terrible idea
since you might log your password to .bash_history... but this should be
fixed soon with self-generating, random passwords.

```
$ mooltipy login tripod.com --login=user_name --password="P@ssw0rd"
```

### Manage Data Contexts
The Mooltipass can be used to securely store small data files! Think ssh or gpg
keys and cryptocurrency wallets.

```
$ mooltipy data import ssh_key ~/.ssh/id_rsa
$ mooltipy data export ssh_key ./restored_key
```

**Warning**: Do not disconnect your mooltipass during data transfer! We do
handle SIGTERM / Ctrl-C to gracefully cancel a transfer.

### Beneath the Mooltipy Wrapper
The mooltipy command is a wrapper for individual utilities. To get help for any
of the individual utilities you can:
```
$ mooltipy data --help
$ mooltipy login --help
```
You can also call any of the utilities directly by prefixing *mp* to the name
of the utility:
```
$ mpdata --help
$ mplogin --help
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

mootipass.do_limited_things()
```
