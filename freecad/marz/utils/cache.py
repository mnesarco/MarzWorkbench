# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileNotice: Part of the Marz addon.

################################################################################
#                                                                              #
#   Copyright (c) 2020 Frank David Martínez Muñoz <mnesarco at gmail.com>      #
#                                                                              #
#   This program is free software: you can redistribute it and / or            #
#   modify it under the terms of the GNU General Public License as             #
#   published by the Free Software Foundation, either version 3 of             #
#   the License, or (at your option) any later version.                        #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU General Public License for more details.                       #
#                                                                              #
#   You should have received a copy of the GNU General Public License          #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                              #
################################################################################

import gc
from time import time
from threading import RLock
from functools import wraps

# !-----------------------------------------------------------------------------
# ! Poor man's cache implementation. Not too good but better than nothing.
# ! This basic cache reduces execution time to half in average.
# !
# ! functools.lru_cache won't work here because I need to support non hashable
# ! function arguments.
# !-----------------------------------------------------------------------------

CACHE_LIFE              = 60*5
MAX_CACHE_SIZE          = 1024
MAIN_CACHE              = {}
CACHE_ENABLED           = True
CACHE_LOCK              = RLock()


def dirtyHash(obj):
    if obj.__hash__:
        return hash(obj)
    else:
        return hash(repr(obj))


def cacheKey(name, *args, **kwargs):
    segs = [name] + [dirtyHash(arg) for arg in args]
    for (kw, arg) in sorted(kwargs.items()):
        segs.append(f"{kw}:{dirtyHash(arg)}")
    return hash((*segs,))


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
# ! This decorator caches any value returned by the function
# ! based on argument values.
# ! This decorator adds a small overhead to the function, so
# ! use it only in costly functions.
def PureFunctionCache(f):
    if CACHE_ENABLED:
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = cacheKey(str(id(f)), *args, **kwargs)
            (cached, _) = MAIN_CACHE.get(key) or (None, 0)
            cleanCache()
            if cached:
                return cached
            else:
                cached = f(*args, **kwargs)
                with CACHE_LOCK:
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
            with CACHE_LOCK:
                MAIN_CACHE[key] = (v, time())
        return (cached, setf)
    else:
        return (None, lambda x: None)
