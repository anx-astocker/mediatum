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
import core.tree as tree
from schema.schema import loadTypesFromDB
from core.acl import AccessData
from core.usergroups import groupoption


class UserGroup(tree.Node):

    def getDescription(self):
        return self.get("description")

    def setDescription(self, d):
        return self.set("description", d)

    def getOption(self):
        return self.get("opts")

    def setOption(self, o):
        return self.set("opts", o)

    def getOptionList(self):
        retList = {}
        myoption = self.getOption()
        for option in groupoption:
            if option.value in myoption:
                retList[option.getName()] = True
            else:
                retList[option.getName()] = False
        return retList

    def getUserNames(self):
        ret = []
        for user in self.getChildren().sort_by_orderpos():
            ret.append(user.getName())
        return ", ".join(ret)

    def getDynamicUserNames(self, as_string=True):
        """return list with names of dynamic users"""
        ret = []
        if self.get("allow_dynamic") == "1":
            _s = self.get("dynamic_users")
            _s = _s.replace(" ", ",").replace("\r", ",").replace("\l", ",").replace("\n", ",")
            ret = ret + [_name.strip() for _name in _s.split(",") if _name.strip()]
        if as_string:
            return ", ".join(ret)
        else:
            return ret

    def getSchemas(self):
        schemas = filter(lambda x: x.isActive(), loadTypesFromDB())
        schemalist = {}
        for user in self.getChildren():
            try:
                for schema in AccessData(user=user).filter(schemas):
                    schemalist[schema.getName()] = "."
            except:
                pass
        schemalist = sorted(schemalist.keys())
        return schemalist

    def getHideEdit(self):
        return self.get("hideedit")

    def setHideEdit(self, value):
        self.set("hideedit", value)

    def isSystemType(self):
        return 1

    def isContainer(self):
        return 1
