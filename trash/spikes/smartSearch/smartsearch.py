# -*- coding: cp1252 -*-
import re

def smartSearchSQL(input):
    #define keywords and OK database fields
    fields = dict(artist="artist", title="name", album="album")
    parts = re.split("(\S+):", input)
    keys = [x for x in parts if parts.index(x)%2 is not 0]
    vals = [x for x in parts if parts.index(x)%2 is 0]
    #how to handle if search words are written before keywords? ignore keywords for now
    if not vals[0]:
        vals.pop(0)
        conditions = [fields[x[0]] + " LIKE '%" + x[1].strip() + "%'" for x in zip(keys,vals) if x[0] in fields]
        cond = "SELECT * FROM collection WHERE (%s)" % (" AND ".join(conditions))
    else:
        cond = " OR ".join([fields[x] + " LIKE '" + vals[0].strip() + "'" for x in fields])
    return "SELECT * FROM collection WHERE (%s)" % cond


test = "artist:kalle jularbo title:sösdala vals invalid:hej"
print smartSearchSQL(test)

test = "overrides artist:kalle jularbo title:sösdala vals"
print smartSearchSQL(test)
