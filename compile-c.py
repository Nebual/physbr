from distutils.core import setup, Extension

description = """A C extension for physbr

Usage:
import physbr
distance = physbr.getdistance((x,y),(x2,y2))
"""

setup (name = 'physbr',
       version = '0.0.1',
       description = 'Physbr C Extensions',
       long_description = description,
        author = "Nebual",
        author_email = "nebual@nebtown.info",
       ext_modules = [Extension('physbr', sources = ['physbr.c'])])