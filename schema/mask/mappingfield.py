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

import re
import core.tree as tree

from core.tree import Node
from core.metatype import Metatype
from utils.utils import esc

class m_mappingfield(Metatype):
    
    def getEditorHTML(self, field, value="", width=400, name="", lock=0, language=None):
        ns = ""
        if field.get("fieldtype")=="mapping":
            field = tree.getNode(field.get("mappingfield"))
            ns = field.getMapping().getNamespace()
            if ns!="":
                ns += ":"
            format = field.getExportFormat()
            field_value = ns + field.getName()
        else:
            format = field.get("mappingfield")
            field_value = field.getName()
            
        for var in re.findall( r'\[(.+?)\]', format ):
            if var.startswith("att:"):
                format = format.replace("[" + var + "]", '<i>{attribute:' + var[4:] + '}</i>')
            elif var=="field":
                format = format.replace("[field]", field_value)
            elif var=="value":
                format = format.replace("[value]", '<i>{' + value + '}</i>')
            elif var=="ns":
                format = format.replace("[value]", '<i>{namspaces}</i>')
                
        format = format.replace("\\t", "")
        return format

    def getFormHTML(self, field, nodes, req):
        return '<b><mappingFormHTML></b><br/>'

    def getMetaHTML(self, parent, index, sub=False, language=None, fieldlist={}):
        return "<mappingfield definition>"
    
    
    def getMetaEditor(self, item, req):
        return "<editor for mappingfield>"

    def isFieldType(self):
        return False

    def replaceVars(self, s, node, attrnode=None, field_value="", options=[]):
        try:
            #if attrnode and node:
            for var in re.findall( r'\[(.+?)\]', s ):
                if var.startswith("att:"):
                    if var=="att:field":
                        s = s.replace("[" + var + "]", attrnode.getName())
                    elif var=="att:id":
                        s = s.replace("[" + var + "]", str(node.id))

                elif var=="field":
                    s = s.replace("[field]", field_value)
                elif var=="value":
                    v = node.get(attrnode.getName())
                    if "t" in options and not v.isdigit():
                        v = '"' + v + '"'                            
                    s = s.replace("[value]", v)
                elif var=="ns":
                    ns = ""
                    for mapping in attrnode.get("exportmapping").split(";"):
                        n = tree.getNode(mapping)
                        if n.getNamespace()!="" and n.getNamespaceUrl()!="":
                            ns += 'xmlns:' + n.getNamespace() + '="' + n.getNamespaceUrl() + '" '
                    s = s.replace("[" + var + "]", ns)
            
            ret = ""        
            for i in range(0, len(s)):
                if s[i-1]=='\\':
                    if s[i]=='r':
                        ret += "\r"
                    elif s[i]=='n':
                        ret += "\n"
                    elif s[i]=='t':
                        ret += "\t"
                elif s[i]=='\\':
                    pass
                else:
                    ret += s[i]
            s = ret
        except:
            pass
        return s
        
        
        
    def getViewHTML(self, fields, nodes, flags, language=""):
        ret = ""
        node = nodes[0]
        
        mask = fields[0].getParents()[0]
        separator = ""

        if mask.getMappingHeader()!="":
            ret += mask.getMappingHeader() + "\r\n"
        
        for field in fields:
            attrnode = tree.getNode(field.get("attribute"))

            if field.get("fieldtype")=="mapping": # mapping to mapping definition
                mapping = tree.getNode(mask.get("exportmapping").split(";")[0])
                separator = mapping.get("separator")
                
                ns = mapping.getNamespace()
                if ns!="":
                    ns += ":"
                fld = tree.getNode(field.get("mappingfield"))
                format = fld.getExportFormat()
                field_value = ns + fld.getName()
            else: # attributes of node
                format = field.get("mappingfield")
                field_value = ""
            
            ret += self.replaceVars(format, node, attrnode, field_value, options=mask.getExportOptions())
            
            if not mask.hasExportOption("l") and list(fields).index(field)<len(fields)-1:
                ret += separator
                
        if mask.getMappingFooter()!="":
            ret += "\r\n" + mask.getMappingFooter()

        return self.replaceVars(ret, node, mask)
    