# This module implements code that makes use of the pickle library to serialize
# (and unserialize) objects to be used across multiple runs of the program.
# The objects are stored in a directory (which is configurable but has a default
# location) that corresponds to the config file being used in the program.

# Imports
import os
import sys
import hashlib
import pickle
import threading

# Library path setup
srcdir = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
if srcdir not in sys.path:
    sys.path.append(srcdir)

# Tool imports
from config import config_load
from utils.utils import *

# Globals
storage_locks = {} # dynamic dictionary of thread locks, indexed by key

def storage_lock(key: str):
    """
    Given a key, retrieves the mutex lock specific to that key for use in
    file reading or writing. If the lock does not yet exist, this function
    creates it and adds it to the dictionary.
    """
    if key not in storage_locks:
        storage_locks[key] = threading.Lock()
    return storage_locks[key]

def storage_config_path():
    """
    Uses the current configurations to determine the path to a directory inside
    which data for this particular config file should be stored.
    If the directory doesn't exist, this function creates it.
    """
    config = config_load()
    if config.path is None:
        panic("Somehow, the current config object has no file path.")

    dname = hashlib.sha512(str(os.path.realpath(config.path)).encode()).hexdigest()
    dpath = os.path.join(os.path.realpath(config.get("storage_dir")), dname)

    # create the directory if it doesn't exist
    if not os.path.isdir(dpath):
        try:
            os.makedirs(dpath, mode=0o700)
        except Exception as e:
            panic("Failed to create data directory for current config.", exception=e)
    return dpath

def storage_obj_path(key: str):
    """
    Takes in a key and generates a unique file path based on the program config.
    The key must be unique.
    """
    dpath = storage_config_path()
    fname = hashlib.sha512(key.encode()).hexdigest() + ".pkl"
    fpath = os.path.join(dpath, fname)
    return fpath

def storage_obj_write(key: str, obj: any, lock=True):
    """
    Takes in a generic object and writes it out to a specific file on disk.
    The location is determined by the current configuration file and the given
    name (key).
    The key must be unique, otherwise it will overwrite another stored object
    with the same key.
    If 'lock' is True, the calling thread will first acquire a lock specific
    to the given key. After writing to the file, the lock is released.
    """
    fpath = storage_obj_path(key)
    
    # acquire the file lock, if applicable
    flock = storage_lock(key) if lock else None
    if lock:
        flock.acquire()
    # write to the file
    with open(fpath, "wb") as fp:
        pickle.dump(obj, fp)
    # release the lock, applicable
    if lock:
        flock.release()

def storage_obj_read(key: str, lock=True):
    """
    Takes in a key and loads the previously-stored object from disk. The object
    is returned on success. If the key doesn't have a corresponding file loaded,
    None is returned instead.
    If 'lock' is True, the calling thread will first acquire a lock specific
    to the given key. After reading from the file, the lock is released.
    """
    fpath = storage_obj_path(key)
    
    if not os.path.isfile(fpath):
        return None

    # acquire the file lock, if applicable
    flock = storage_lock(key) if lock else None
    if lock:
        flock.acquire()
    
    # read the file's contents
    data = None
    with open(fpath, "rb") as fp:
        data = pickle.load(fp)
    
    # release the lock, applicable
    if lock:
        flock.release()
    return data

