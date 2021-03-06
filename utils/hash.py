"""
 mediatum - a multimedia content repository

 Copyright (C) 2007 Arne Seifert <seiferta@in.tum.de>
 Copyright (C) 2007 Matthias Kramm <kramm@in.tum.de>

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import core.tree as tree
import hashlib


def calcChecksum(filename, method):
    if os.path.exists(filename):
        f = open(filename)
        if method == "SHA-1":
            h = hashlib.sha1()
        else:
            h = hashlib.new('ripemd160')
        h.update(f.read())
        f.close()
        return h.hexdigest()
    else:
        return ""


def calcChecksumFromMetadata(node):
    h = hashlib.sha1()
    h.update(node.id)
    h.update(node.getName())

    def attributesToString(node):
        string = ""
        for item in node.items():
            string += item[0] + item[1]
        return string

    h.update(attributesToString(node))

    return h.hexdigest()


def getChecksum(nodeId, method="SHA-1", filepath=""):
    if method not in ["SHA-1", "RIPEMD-160"]:
        raise AttributeError("This method is not supported for checksum calculation: " + method)
    try:
        if filepath != "" and os.path.exists(filepath):
            return calcChecksum(filepath, method)
        else:
            node = tree.getNode(nodeId)
            for f in node.getFiles():
                if f.getType() == node.getOriginalTypeName():
                    return calcChecksum(f.retrieveFile(), method)
            return calcChecksumFromMetadata(node)

    except tree.NoSuchNodeError as e:
        print "Node not present in mediaTUM:", e
    except IOError as e:
        print "File doesn't exist on filesystem", e
    except Exception:
        print "Error occured in hash.getChecksum"
