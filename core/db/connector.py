#!/usr/bin/python
"""
 mediatum - a multimedia content repository

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

import logging

from utils import *
import msgpack

debug = 0
log = logging.getLogger('database')


class Connector:

    def esc(self, text):
        return "'" + text.replace("'", "\\'") + "'"

    def removeChild(self, nodeid, childid):
        self.runQuery("delete from nodemapping where nid=" + nodeid + " and cid=" + childid)

    def getChildren(self, nodeid):
        t = self.runQuery("select cid from nodemapping where nid=" + nodeid + " order by cid")
        idlist = []
        for id in t:
            idlist += [str(id[0])]
        return idlist

    def get_children_with_type(self, parent_id, nodetype):
        sql = ("select cid from node, nodemapping"
               " where nid=%s and id=cid and type=%s"
               " order by cid")
        t = self.runQuery(sql, parent_id, nodetype)

        return [str(i[0]) for i in t]

    def get_num_children(self, nodeid):
        t = self.runQuery("select count(*) from nodemapping where nid=" + nodeid)
        return t[0][0]

    def getContainerChildren(self, nodeid):
        t = self.runQuery("select cid from containermapping where nid=" + nodeid + " order by cid")
        idlist = []
        for id in t:
            idlist += [str(id[0])]
        return idlist

    def getContentChildren(self, nodeid):
        t = self.runQuery("select cid from contentmapping where nid=" + nodeid + " order by cid")
        idlist = []
        for id in t:
            idlist += [str(id[0])]
        return idlist

    def getParents(self, nodeid):
        t = self.runQuery("select nid from nodemapping where cid=" + nodeid)
        idlist = []
        for id in t:
            idlist += [str(id[0])]
        return idlist

    def getAttributes(self, nodeid):
        t = self.runQuery("select name,value from nodeattribute where nid=" + nodeid)
        attributes = {}
        for name, value in t:
            if value:
                attributes[name] = value
        return attributes

    def get_all_attribute_values(self, attribute, schema, distinct=False):
        value_sql = "distinct(value)" if distinct else "value"
        sql = ("SELECT node.id, " + value_sql + " from node, nodeattribute"
               " WHERE node.id=nodeattribute.nid"
               " AND nodeattribute.name=%s"
               " AND node.type LIKE %s")
        return self.runQuery(sql, attribute, "%/" + schema)

    def get_attributes_complex(self, nodeid):
        t = self.runQuery("select name,value from nodeattribute where nid=%s", nodeid)
        attributes = {}
        mloads = msgpack.loads
        for name, value in t:
            if value.startswith("\x11PACK\x12"):
                attributes[name] = mloads(value[6:], encoding="utf8")
            else:
                attributes[name] = unicode(value, encoding="utf8")
        return attributes

    def getMetaFields(self, name):
        return self.runQuery("select value from nodeattribute where name=" + self.esc(name))

    def getSortOrder(self, field):
        if field == "nodename":
            return self.runQuery("select id,name from node")
        else:
            return self.runQuery("select nid,value from nodeattribute where name=" + self.esc(field))

    def getActiveACLs(self):
        mylist = self.runQuery("select distinct readaccess from node where readaccess not like '{user %}'")
        acls = []
        for acl in mylist:
            acls += acl[0].split(',')
        return acls

    def getFiles(self, nodeid):
        return self.runQuery("select filename,type,mimetype from nodefile where nid=" + nodeid)

    def removeFile(self, nodeid, path):
        self.runQuery("delete from nodefile where nid = " + nodeid + " and filename=" + self.esc(path))

    def removeSingleFile(self, nodeid, path):
        self.runQuery("delete from nodefile where nid = " + nodeid + " and filename=" + self.esc(path))

    def removeAttribute(self, nodeid, attname):
        self.runQuery("delete from nodeattribute where nid=" + nodeid + " and name=" + self.esc(attname))

    def setDirty(self, nodeid):
        self.runQuery("update node set dirty=1 where id=" + str(nodeid))

    def cleanDirty(self, nodeid):
        self.runQuery("update node set dirty=0 where id=" + str(nodeid))

    def isDirty(self, nodeid):
        return self.runQuery("select dirty from node where id=" + str(nodeid))[0][0]

    def getDirty(self, limit=0):
        if limit:
            ids = self.runQuery("select id from node where dirty=1 limit %s", limit)
        else:
            ids = self.runQuery("select id from node where dirty=1")
        ids2 = [id[0] for id in ids]
        return ids2

    def getDirtySchemas(self, limit=0):
        dirty_nodes = self.getDirty()
        # get all nodes with type like %/%
        schema_nodes = self.get_nids_by_type_suffix("/%")
        dirty_schema_nodes = list(set(schema_nodes).intersection(dirty_nodes))
        if limit:
            return dirty_schema_nodes[:limit]
        else:
            return dirty_schema_nodes

    def setNodeName(self, id, name):
        self.runQuery("update node set name = " + self.esc(name) + " where id = " + id)

    def setNodeOrderPos(self, id, orderpos):
        self.runQuery("update node set orderpos = " + str(orderpos) + " where id = " + id)

    def setNodeLocalRead(self, id, localread):
        self.runQuery("update node set localread = " + self.esc(localread) + " where id = " + id)

    def setNodeReadAccess(self, id, access):
        self.runQuery("update node set readaccess = " + self.esc(access) + " where id = " + id)

    def setNodeWriteAccess(self, id, access):
        self.runQuery("update node set writeaccess = " + self.esc(access) + " where id = " + id)

    def setNodeDataAccess(self, id, access):
        self.runQuery("update node set dataaccess = " + self.esc(access) + " where id = " + id)

    def setNodeType(self, id, type):
        self.runQuery("update node set type = " + self.esc(type) + " where id = " + id)

    def getMappings(self, direction):
        if direction > 0:
            return self.runQuery("select nid,cid from nodemapping order by nid,cid")
        else:
            return self.runQuery("select cid,nid from nodemapping order by cid,nid")

    # core node methodes
    def getRootID(self):
        nodes = self.runQuery("select id from node where type='root'")
        if len(nodes) <= 0:
            return None
        if len(nodes) > 1:
            raise Exception("More than one root node")
        return str(nodes[0][0])

    def getNode(self, id):
        t = self.runQuery("select id,name,type,readaccess,writeaccess,dataaccess,orderpos,localread from node where id=" + str(id))
        if len(t) == 1:
            # id,name,type,read,write,data,orderpos,localread
            return str(t[0][0]), t[0][1], t[0][2], t[0][3], t[0][4], t[0][5], t[0][6], t[0][7]
        elif len(t) == 0:
            log.error("No node for ID " + str(id))
            return None
        else:
            log.error("More than one node for id " + str(id))
            return None

    def getNodeIdByAttribute(self, attributename, attributevalue):
        if attributename.endswith("access"):
            t = self.runQuery("select id from node where " + attributename + " like %s", "%" + attributevalue + "%")
        else:
            if attributevalue == "*":
                t = self.runQuery("select node.id from node, nodeattribute where node.id=nodeattribute.nid and nodeattribute.name=%s",
                                  attributename)
            else:
                t = self.runQuery("select node.id from node, nodeattribute "
                                  "where node.id=nodeattribute.nid and nodeattribute.name=%s and nodeattribute.value=%s",
                                  attributename, attributevalue)
        if len(t) == 0:
            return []
        else:
            ret = []
            for i in t:
                if i[0] not in ret:
                    ret.append(i[0])
            return ret

    def getNamedNode(self, parentid, name):
        t = self.runQuery("select id from node,nodemapping where node.name=" + self.esc(name) +
                          " and node.id = nodemapping.cid and nodemapping.nid = " + parentid)
        if len(t) == 0:
            t = self.runQuery("select id from node,nodemapping where node.type=" + self.esc(name) +
                              " and node.id = nodemapping.cid and nodemapping.nid = " + parentid)
            if len(t) == 1:
                return t[0][0]
            else:
                return None
        else:
            return t[0][0]

    def getNamedTypedNode(self, parentid, name, nodetype):
        query = ("select id from node,nodemapping"
                 " where node.name={}"
                 " and node.type={}"
                 " and nodemapping.nid = {}"
                 " and node.id = nodemapping.cid"
                 .format(self.esc(name), self.esc(nodetype), parentid))
        t = self.runQuery(query)
        if len(t) == 1:
            return t[0][0]
        else:
            return None

    def get_nids_by_type_suffix(self, type_suffix):
        """Gets node ids with a type with suffix `type_suffix`
        """
        sql = ("SELECT id"
               " FROM node"
               " WHERE type LIKE %s")
        res = self.runQuery(sql, "%" + type_suffix)
        if res:
            return [r[0] for r in res]

    def deleteNode(self, id):
        self.runQuery("delete from node where id=" + id)
        self.runQuery("delete from nodemapping where cid=" + id)
        self.runQuery("delete from nodeattribute where nid=" + id)
        self.runQuery("delete from nodefile where nid=" + id)

        # WARNING: this might create orphans
        self.runQuery("delete from nodemapping where nid=" + id)
        log.info("node " + id + " deleted")

    def mkOrderPos(self):
        t = self.runQuery("select max(orderpos) as orderpos from node")
        if len(t) == 0 or t[0][0] is None:
            return "1"
        orderpos = t[0][0] + 1
        return orderpos

    def mkID(self):
        t = self.runQuery("select max(id) as maxid from node")
        if len(t) == 0 or t[0][0] is None:
            return "1"
        id = t[0][0] + 1
        return str(id)

    def get_aliased_nid(self, alias):
        """Get node id which belongs to the given alias path"""
        sql = ("SELECT nid"
               " FROM nodeattribute"
               " WHERE name='system.aliascol'"
               " AND value=%s")
        res = self.runQuery(sql, alias)
        if res:
            return int(res[0][0])

    # node sorting

    def _sql_sort_field_name_and_dir(self, f):
        """Convert node field name to escaped name and sort direction."""
        if f.startswith("-"):
            direction = " DESC"
            fname = f[1:]
        else:
            direction = " ASC"
            fname = f
        return (self.esc(fname), direction)

    def sort_nodes_by_fields(self, nids, fields):
        """Sorts nodes by field (attribute) values.
        :param nids: node ids
        :param fields: field names to sort for. Prepend - to sort descending
        """
        raise NotImplementedError()
