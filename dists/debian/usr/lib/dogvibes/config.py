import sys, re
# -- Loads a config file, creates and returns a dictionary
def load(filename):
     # Try to open a file handle on the config file and read the text
     # Possible exception #1 - the file might not be found
     # Possible exception #2 - the file might have read-protection
     try: configfile = open(filename, "r")
     except Exception, e: raise
     try: configtext = configfile.read()
     except Exception, e: raise
     # Compile a pattern that matches our key-value line structure
     pattern = re.compile("\\n([\w_]+)[\t ]*([\w: \\\/~.-]+)")
     # Find all matches to this pattern in the text of the config file
     tuples = re.findall(pattern, configtext)
     # Create a new dictionary and fill it: for every tuple (key, value) in
     # the 'tuples' list, set ret[key] to value 
     ret = dict()
     for x in tuples: ret[x[0]] = x[1]
     # Return the fully-loaded dictionary object
     return ret
