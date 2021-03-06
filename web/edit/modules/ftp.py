"""
 mediatum - a multimedia content repository

 Copyright (C) 2010 Arne Seifert <seiferta@in.tum.de>

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
import core.acl as acl
import core.users as users
import core.config as config

from schema.schema import loadTypesFromDB
from core.datatypes import loadAllDatatypes
from core.translation import translate, lang, t
from core.transition import httpstatus

def getContent(req, ids):
    user = users.getUserFromRequest(req)
    if "ftp" in users.getHideMenusForUser(user):
        req.setStatus(httpstatus.HTTP_FORBIDDEN)
        return req.getTAL("web/edit/edit.html", {}, macro="access_error")
    
    ids = ids[0] # use only first selected node
    node = tree.getNode(ids)
    error = ""
    
    def processFile(node, file, ftype):
        nname = file.retrieveFile().split("/")
        nname = "/".join(nname[:-1])+"/"+nname[-1][4:]
        try:
            os.rename(file.retrieveFile(), nname)
        except:
            nname = file.retrieveFile()
        fnode = tree.Node(nname.split("/")[-1], ftype)
        node.removeFile(file)
        file._path = file._path.replace(config.get("paths.datadir"), "")
        file._path = "/".join(file._path.split("/")[:-1]) + "/"+fnode.getName()
        fnode.addFile(file)
        fnode.event_files_changed()
        node.addChild(fnode)
        return fnode
    
    for key in req.params.keys():
        if key.startswith("process|"): # process selected file (single)
            fname = key[:-2].split("|")[-1]
            ftype = req.params.get("schema").replace(";","")
            if ftype!="":
                for f in node.getFiles():
                    if f.getName()==fname:
                        processFile(node, f, ftype)
                        break
                break
            else:
                error = "edit_ftp_error1"
                
        elif key.startswith("del|"):
            for f in node.getFiles():
                if f.getName()==key[4:-2]:
                    node.removeFile(f)
                    break
            break
            
        elif key.startswith("delall"): # delete all selected files
            delfiles = [f.split("|")[-1] for f in req.params.get("selfiles").split(";")]
            
            for f in node.getFiles():
                if f.getName() in delfiles:
                    node.removeFile(f)
            
            break
            
        elif key.startswith("processall"): # process all selected files
            for file in req.params.get("selfiles", "").split(";"):
                if file:
                    ftype, fname = file.split("|")
                    if "multschema|"+ftype in req.params and req.params.get("multschema|"+ftype)!="":
                        for f in node.getFiles():
                            if f.getName()==fname:
                                print "use", ftype+"/"+req.params.get("multschema|"+ftype)
                                processFile(node, f, ftype+"/"+req.params.get("multschema|"+ftype) )
                                break
                    else:
                        error = "edit_ftp_error2"
                        break
            break
            
    files = filter(lambda x: x.getName().startswith("ftp_"), node.getFiles())
    types = []
    for f in files:
        if f.getType() not in types:
            if f.getType() != "other":
                types.append(f.getType())

    dtypes = {}
    for scheme in filter(lambda x: x.isActive(), acl.AccessData(req).filter(loadTypesFromDB())):
        for dtype in scheme.getDatatypes():
            if dtype not in dtypes.keys():
                dtypes[dtype] = []
            if scheme not in dtypes[dtype]:
                dtypes[dtype].append(scheme)
    
    for t in dtypes:
        dtypes[t].sort(lambda x, y: cmp(translate(x.getLongName(), request=req).lower(), translate(y.getLongName(), request=req).lower()))
    
    access = acl.AccessData(req)
    if not access.hasWriteAccess(node):
        req.setStatus(httpstatus.HTTP_FORBIDDEN)
        return req.getTAL("web/edit/edit.html", {}, macro="access_error")
    
    v = {}
    v['error'] = error
    v['files'] = files
    v['node'] = node
    v['schemes'] = dtypes # schemes
    v['usedtypes'] = types
    v['tab'] = req.params.get("tab", "")
    v['ids'] = ids
    v["script"] = "<script> parent.reloadTree('"+req.params.get("id")+"');</script>"
    
    return req.getTAL("web/edit/modules/ftp.html", v, macro="edit_ftp")


# used in plugins?
def adduseropts(user):
    ret = []
    
    dtypes = {}
    for scheme in filter(lambda x: x.isActive(), acl.AccessData(user=user).filter(loadTypesFromDB())):
        for dtype in scheme.getDatatypes():
            if dtype not in dtypes.keys():
                dtypes[dtype] = []
            if scheme not in dtypes[dtype]:
                dtypes[dtype].append(scheme)
    
    i = [x.getLongName() for x in dtypes['image']]
    i.sort()
    
    field = tree.Node("ftp.type_image", "metafield")
    field.set("label", "ftp_image_schema")
    field.set("type", "list")
    field.set("valuelist", "\r\n".join(i))
    ret.append(field)
    
    d = [x.getLongName() for x in dtypes['document']]
    d.sort()
    
    field = tree.Node("ftp.type_document", "metafield")
    field.set("label", "ftp_document_schema")
    field.set("type", "list")
    field.set("valuelist", "\r\n".join(d))
    ret.append(field)

    return ret