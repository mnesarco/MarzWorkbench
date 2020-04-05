# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"

import gc
import hashlib
from time import time
from marz_freecad import isVersion19

#!-----------------------------------------------------------------------------
#! Poor man's cache implementation. Not too good but better than nothing.
#! This basic cache reduces execution time to half in average.
#!-----------------------------------------------------------------------------

CACHE_LIFE              = 60*5
MAX_CACHE_SIZE          = 100
MAIN_CACHE              = {}
CACHE_ENABLED           = True

def cacheKey(name, *args, **kwargs):
    segs = [name] + [repr(arg) for arg in args]
    for (kw, arg) in sorted(kwargs.items()):
        segs.append(f"{kw}:{repr(arg)}")
    return hashlib.md5('|'.join(segs).encode()).hexdigest()

def cleanCache():
    global MAIN_CACHE
    cacheSize = len(MAIN_CACHE)
    if cacheSize >= MAX_CACHE_SIZE:
        clean = {}
        now = time()
        for key, item in MAIN_CACHE.items():
            (value, ts) = item
            if now - ts < CACHE_LIFE:
                clean[key] = item
        MAIN_CACHE = clean
        gc.collect()
        newCacheSize = len(clean)
        if newCacheSize < cacheSize:
            print(f"[MARZ] Cache cleaning {cacheSize} objects => {newCacheSize} objects\n")

# Function Decorator
#! This decorator caches any value returned by the function
#! based on argument values.
#! This decorator adds a small overhead to the function, so
#! use it only in costly functions.
def PureFunctionCache(f):
    if CACHE_ENABLED:
        def wrapper(*args, **kwargs):
            key = cacheKey(str(id(f)), *args, **kwargs)
            (cached, _) = MAIN_CACHE.get(key) or (None, 0)
            cleanCache()
            if cached:
                return cached
            else:
                cached = f(*args, **kwargs)
                MAIN_CACHE[key] = (cached, time())
                return cached
        return wrapper
    else:
        return f

def getCachedObject(baseName, *args):
    """This function is for direct calls to cache
    when writing a Pure Function is too difficult or
    ugly, so we can cache portions of code based on dependencies.
    
    Arguments:
        baseName {str} -- Object Name
        *args -- vales, different values lead to different cached object.
    
    Returns:
        {tuple} -- (cachedObject, updateFunction)
    """
    if CACHE_ENABLED:
        key = cacheKey(baseName, *args)
        (cached, ts) = MAIN_CACHE.get(key) or (None, 0)    
        cleanCache()
        def setf(v):
            MAIN_CACHE[key] = (v, time())
        return (cached, setf)
    else:
        return (None, lambda x: None)
