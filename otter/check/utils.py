"""
Utils for Otter Check
"""

import time
import hashlib

from IPython import get_ipython
from IPython.display import display, Javascript

def save_notebook(filename, timeout=10):
    """
    Force-saves a Jupyter notebook by displaying JavaScript.

    Args:
        filename (``str``): path to notebook file being saved
        timeout (``int`` or ``float``): number of seconds to wait for save before timing-out
    
    Returns
        ``bool``: whether the notebook was saved successfully
    """
    timeout = timeout * 10**9
    if get_ipython() is not None:
        f = open(filename, "rb")
        md5 = hashlib.md5(f.read()).hexdigest()
        start = time.time_ns()
        display(Javascript("Jupyter.notebook.save_checkpoint();"))
        
        curr = md5
        while curr == md5 and time.time_ns() - start <= timeout:
            time.sleep(1)
            f.seek(0)
            curr = hashlib.md5(f.read()).hexdigest()
        
        f.close()

        return curr != md5
    
    return True
