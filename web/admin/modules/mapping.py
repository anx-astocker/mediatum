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

from schema.mapping import getMappings, getMapping, updateMapping, deleteMapping, updateMappingField, deleteMappingField
from web.admin.adminutils import Overview, getAdminStdVars
from core.translation import lang, t



def validate(req, op):

    print req.params

    for key in req.params.keys():
 
        if key.startswith("fieldlist_"):
            # list all defined fields
            return viewlist(req, key[10:-2])

        elif key.startswith("newfield_"):
            # create new mapping field
            return editMappingField_mask(req, "", tree.getNode(key[9:-2]))
            
        elif key.startswith("editfield_"):
            # create new mapping field
            node = tree.getNode(key[10:-2])
            for p in node.getParents():
                if p.type=="mapping":
                    return editMappingField_mask(req, key[10:-2], p)
        
        elif key.startswith("deletefield_"):
                # delete mapping field
                deleteMappingField(key[12:-2])
                break   
        
        
        elif key.startswith("new"):
            # create new mapping
            return editMapping_mask(req, "")
            
        elif key.startswith("edit_"):
            # edit/create mapping
            return editMapping_mask(req, str(key[key.index("_")+1:-2]))
            
        elif key.startswith("delete_"):
                # delete mapping
                deleteMapping(key[7:-2])
                break   
        
        elif key == "form_op":
            if req.params["form_op"]=="save_new" or req.params["form_op"]=="save_edit":
                # save mapping values
                if str(req.params["name"])=="":
                    return editMapping_mask(req, "", 1) # empty required field
                else:
                    updateMapping(req.params.get("name"), namespace=req.params.get("namespace"), namespaceurl=req.params.get("namespaceurl"), description=req.params.get("description"), header=req.params.get("header"), footer=req.params.get("footer"), separator=req.params.get("separator"), standardformat=req.params.get("standardformat"), id=req.params.get("id"))
                break
                
                
            if req.params["form_op"]=="save_new_field" or req.params["form_op"]=="save_edit_field":
                # save mapping field values
                if str(req.params["name"])=="":
                    return editMappingField_mask(req, "", req.params.get("parent"), 1) # empty required field
                else:
                    _mandatory = False
                    if "mandatory" in req.params.keys():
                        _mandatory = True
                    updateMappingField(req.params.get("parent"), req.params.get("name"), description=req.params.get("description"), exportformat=req.params.get("exportformat"), mandatory=_mandatory, id=req.params.get("id"))
                    return viewlist(req, req.params.get("parent"))
                break

    if "detailof" in req.params.keys():
        return viewlist(req, req.params.get("detailof"))

    return view(req)

    
    
def view(req):
    mappings = list(getMappings())
    pages = Overview(req, mappings)
    order = req.params.get("order","")

    # sorting
    if order != "":
        if int(order[0:1])==0:
            mappings.sort(lambda x, y: cmp(x.getName().lower(),y.getName().lower()))
        elif int(order[0:1])==1:
            mappings.sort(lambda x, y: cmp(x.getNamespace().lower(),y.getNamespace().lower()))    
        elif int(order[0:1])==2:
            mappings.sort(lambda x, y: cmp(x.getNamespaceUrl().lower(),y.getNamespaceUrl().lower()))
        elif int(order[0:1])==3:
            mappings.sort(lambda x, y: cmp(x.getDescription().lower(),y.getDescription().lower()))
        elif int(order[0:1])==4:   
            mappings.sort(lambda x, y: cmp(len(x.getFields()),len(y.getFields())))
            
        if int(order[1:])==1:
            mappings.reverse()
    else:
        mappings.sort(lambda x, y: cmp(x.getName().lower(),y.getName().lower()))
    
    v = getAdminStdVars(req)
    v["sortcol"] = pages.OrderColHeader([t(lang(req),"admin_mapping_col_1"), t(lang(req),"admin_mapping_col_2"), t(lang(req),"admin_mapping_col_3"), t(lang(req),"admin_mapping_col_4"), t(lang(req),"admin_mapping_col_5")])
    v["mappings"] = mappings
    v["options"] = []
    v["pages"] = pages
    return req.getTAL("web/admin/modules/mapping.html", v, macro="view")
    
    
    
    
def editMapping_mask(req, id, err=0):
    if err==0 and id=="":
        # new mapping
        mapping = tree.Node("", type="mapping")
    elif id!="":
        # edit mapping
        mapping = getMapping(id)
    else:
        # error while filling values
        mapping = tree.Node("", type="mapping")
        mapping.setName(req.params.get("name",""))
        mapping.setDescription(req.params.get("description",""))
        mapping.setNamespace(req.params.get("namespace",""))
        mapping.setNamespaceUrl(req.params.get("namespaceurl",""))
        mapping.setHeader(req.params.get("header"))
        mapping.setFooter(req.params.get("footer"))
        mapping.setSeparator(req.params.get("separator"))
        mapping.setStandardFormat(req.params.get("standardformat"))

    v = getAdminStdVars(req)
    v["error"] = err
    v["mapping"] = mapping
    v["id"] = id
    return req.getTAL("web/admin/modules/mapping.html", v, macro="modify")

    
def viewlist(req, id):
    mapping = getMapping(id)

    fields = list(mapping.getFields())
    pages = Overview(req, fields)
    order = req.params.get("order","")

    # sorting
    if order != "":
        if int(order[0:1])==0:
            fields.sort(lambda x, y: cmp(x.getName().lower(),y.getName().lower()))
        elif int(order[0:1])==1:
            fields.sort(lambda x, y: cmp(x.getDescription().lower(),y.getDescription().lower()))
        elif int(order[0:1])==2:
            fields.sort(lambda x, y: cmp(x.getMandatory(),y.getMandatory()))
            
        if int(order[1:])==1:
            fields.reverse()
    else:
        fields.sort(lambda x, y: cmp(x.getName().lower(),y.getName().lower()))
    
    v = getAdminStdVars(req)
    v["sortcol"] = pages.OrderColHeader([t(lang(req),"admin_mappingfield_col_1"), t(lang(req),"admin_mappingfield_col_2"), t(lang(req),"admin_mappingfield_col_3") ], addparams="&detailof="+str(mapping.id))
    v["fields"] = fields
    v["mapping"] = mapping
    v["options"] = []
    v["pages"] = pages

    return req.getTAL("web/admin/modules/mapping.html", v, macro="viewlist")

    
def editMappingField_mask(req, id, parent, err=0):
    if err==0 and id=="":
        # new mapping field
        field = tree.Node("", type="mappingfield")
    elif id!="":
        # edit mapping field
        field = tree.getNode(id)
    else:
        #error while filling values
        field = tree.Node("", type="mappingfield")
        field.setName(req.params.get("name",""))
        field.setDescription(req.params.get("description",""))
        field.setExportFormat(req.params.get("exportformat",""))
        if "mandatory" in req.params.keys():
            field.setMandatory("True")
            

    v = getAdminStdVars(req)
    v["error"] = err
    v["field"] = field
    v["parent"] = parent
    v["id"] = id
    return req.getTAL("web/admin/modules/mapping.html", v, macro="modifyfield")
    