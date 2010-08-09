import sys
import os
import tagpy # requires deb python-tagpy

for top, dirnames, filenames in os.walk("/home/brizz/music"):
    for filename in filenames:
        if filename.endswith('.mp3'):
            f = tagpy.FileRef(os.path.join(top, filename))
            print f.tag().title
