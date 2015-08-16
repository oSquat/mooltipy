# Mooltipy
A Mooltipass Python library and command line management utilities.

Under heavy development. I just got my unit a few days ago.

## Installation & Usage
Install pip dependencies from requirements.txt or through a virtual environment.

```
user@box:~/mooltipy/$ virtualenv ./env
user@box:~/mooltipy/$ . ./env/bin/activate
(env)user@box:~/mooltipy/$ pip install -r ./requirements.txt
(env)user@box:~/mooltipy/$ sudo ./env/bin/python ./example.py
```

### Add contexts
You can use mooltipass to add contexts. This is a terrible idea in practice
since you might log your password to .bash_history... but this should be
expanded soon.

```
$ mooltipass tripod.com --login=user_name --password="P@ssw0rd"
```

### Manage Data Contexts
The Mooltipass can be used to securely store small data files!

```
$ mpdata import ssh_key ~/.ssh/id_rsa
$ mpdata export ssh_key ./restored_key
```

### Using the Mooltipass module
To utilize the class:
```python
from mooltipy import Mooltipass

import sys

mooltipass = MooltipassClient()

if mooltipass.ping():
    print('Connected to the mooltipass!')
else:
    print('Failed to connect to mooltipass.')
    sys.exit(0)

mootipass.do_limited_things()

```

## Notes
Based on a copy-paste-modify from [mooltipass_comms](https://github.com/limpkin/mooltipass/tree/master/tools/python_comms), development code written in Python by the Mooltipass team.
