# Mooltipy
A Mooltipass Python library.

## Installation & Usage
Install pip dependencies from requirements.txt or through a virtual environment.

```
user@box:~/mooltipy/$ virtualenv ./env
user@box:~/mooltipy/$ . ./env/bin/activate
(env)user@box:~/mooltipy/$ pip install -r ./requirements.txt
(env)user@box:~/mooltipy/$ sudo ./env/bin/python ./mooltipy_example.py
```

To utilize the class:
```python
from mooltipy import *

import sys

mooltipass = Mooltipass()

if mooltipass.ping():
    print('Connected to the mooltipass!')
else:
    print('Failed to connect to mooltipass.')
    sys.exit(0)

mootipass.do_awesome_future_stuff()

```

## Notes
Based on a copy-paste-modify from [mooltipass_comms](https://github.com/limpkin/mooltipass/tree/master/tools/python_comms), development code written in Python by the Mooltipass team.
