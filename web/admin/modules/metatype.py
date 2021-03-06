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
import sys
import core.tree as tree

from core.datatypes import loadAllDatatypes, loadNonSystemTypes
from web.admin.adminutils import Overview, getAdminStdVars, getSortCol, getFilter
from core.tree import getNode, searcher
from web.common.acl_web import makeList
from utils.utils import removeEmptyStrings, esc
from core.translation import lang, t
from core.acl import AccessData
from schema.schema import loadTypesFromDB, getMetaFieldTypeNames, getMetaType, updateMetaType, existMetaType, deleteMetaType, fieldoption, moveMetaField, getMetaField, deleteMetaField, getFieldsForMeta, dateoption, requiredoption, existMetaField, updateMetaField, generateMask, cloneMask, exportMetaScheme, importMetaSchema
from schema.schema import VIEW_DEFAULT
from schema.bibtex import getAllBibTeXTypes
from schema import citeproc

from utils.fileutils import importFileToRealname
# metafield methods
from .metatype_field import showDetailList, FieldDetail
# meta mask methods
from .metatype_mask import showMaskList, MaskDetails

from contenttypes.default import flush_maskcache


def getInformation():
    return {"version": "1.0"}

""" checks a string whether it only contains the alphanumeric chars as well as "-" "." """


def checkString(string):
    result = re.match("([\w\-\.]+)", string)
    if result is not None and result.group(0) == string:
        return True
    return False


""" standard method for admin module """


def validate(req, op):
    path = req.path[1:].split("/")

    if len(path) == 3 and path[2] == "overview":
        return showFieldOverview(req)

    if len(path) == 4 and path[3] == "editor":
        res = showEditor(req)
        # mask may have been edited: flush masks cache
        flush_maskcache(req=req)
        return res

    if len(path) == 5 and path[3] == "editor" and path[4] == "show_testnodes":

        template = req.params.get('template', '')
        testnodes_list = req.params.get('testnodes', '')
        width = req.params.get('width', '400')
        item_id = req.params.get('item_id', None)

        mdt_name = path[1]
        mask_name = path[2]

        mdt = tree.getRoot('metadatatypes').getChild(mdt_name)
        mask = mdt.getChild(mask_name)

        access = AccessData(req)

        sectionlist = []
        for nid in [x.strip() for x in testnodes_list.split(',') if x.strip()]:
            section_descr = {}
            section_descr['nid'] = nid
            section_descr['error_flag'] = ''  # in case of no error
            try:
                node = tree.getNode(nid)
                section_descr['node'] = node
                if access.hasAccess(node, "data"):
                    try:
                        node_html = mask.getViewHTML([node], VIEW_DEFAULT, template_from_caller=[template, mdt, mask, item_id], mask=mask)
                        section_descr['node_html'] = node_html
                    except:
                        error_text = str(sys.exc_info()[1])
                        template_line = 'for node id ' + str(nid) + ': ' + error_text
                        try:
                            m = re.match(r".*line (?P<line>\d*), column (?P<column>\d*)", error_text)
                            if m:
                                mdict = m.groupdict()
                                line = int(mdict.get('line', 0))
                                column = int(mdict.get('column', 0))
                                error_text = error_text.replace('line %d' % line, 'template line %d' % (line - 1))
                                template_line = 'for node id ' + str(nid) + '<br/>' + error_text + '<br/><code>' + esc(template.split(
                                    "\n")[line - 2][0:column - 1]) + '<span style="color:red">' + esc(template.split("\n")[line - 2][column - 1:]) + '</span></code>'
                        except:
                            pass
                        section_descr['error_flag'] = 'Error while evaluating template:'
                        section_descr['node_html'] = template_line
                else:
                    section_descr['error_flag'] = 'no access'
                    section_descr['node_html'] = ''
            except tree.NoSuchNodeError:
                section_descr['node'] = None
                section_descr['error_flag'] = 'NoSuchNodeError'
                section_descr['node_html'] = 'for node id ' + str(nid)
            sectionlist.append(section_descr)

        # remark: error messages will be served untranslated in English
        # because messages from the python interpreter (in English) will be added

        return req.getTAL("web/admin/modules/metatype.html", {'sectionlist': sectionlist}, macro="view_testnodes")

    if len(path) == 2 and path[1] == "info":
        return showInfo(req)

    if "file" in req.params and hasattr(req.params["file"], "filesize") and req.params["file"].filesize > 0:
        # import scheme from xml-file
        importfile = req.params.get("file")
        if importfile.tempname != "":
            xmlimport(req, importfile.tempname)

    if req.params.get("acttype", "schema") == "schema":
        # section for schema
        for key in req.params.keys():
            # create new metadatatype
            if key.startswith("new"):
                return MetatypeDetail(req, "")

            # edit metadatatype
            elif key.startswith("edit_"):
                return MetatypeDetail(req, str(key[5:-2]))

            # delete metadata
            elif key.startswith("delete_"):
                deleteMetaType(key[7:-2])
                break

            # show details for given metadatatype
            elif key.startswith("detaillist_"):
                return showDetailList(req, str(key[11:-2]))

            # show masklist for given metadatatype
            elif key.startswith("masks_"):
                return showMaskList(req, str(key[6:-2]))

            # reindex search index for current schema
            elif key.startswith("indexupdate_") and "cancel" not in req.params.keys():
                schema = tree.getNode(key[12:])
                searcher.reindex(schema.getAllItems())
                break

        # save schema
        if "form_op" in req.params.keys():
            if req.params.get("form_op", "") == "cancel":
                return view(req)

            if req.params.get("mname", "") == "" or req.params.get("mlongname", "") == "" or req.params.get("mdatatypes", "") == "":
                return MetatypeDetail(req, req.params.get("mname_orig", ""), 1)  # no name was given
            elif not checkString(req.params.get("mname", "")):
                return MetatypeDetail(req, req.params.get("mname_orig", ""), 4)  # if the name contains wrong characters
            elif req.params.get("mname_orig", "") != req.params.get("mname", "") and existMetaType(req.params.get("mname")):
                return MetatypeDetail(req, req.params.get("mname_orig", ""), 2)  # metadata still existing

            _active = 0
            if req.params.get("mactive", "") != "":
                _active = 1
            updateMetaType(req.params.get("mname", ""),
                           description=req.params.get("description", ""),
                           longname=req.params.get("mlongname", ""), active=_active,
                           datatypes=req.params.get("mdatatypes", "").replace(";", ", "),
                           bibtexmapping=req.params.get("mbibtex", ""),
                           citeprocmapping=req.params.get("mciteproc", ""),
                           orig_name=req.params.get("mname_orig", ""))
            mtype = getMetaType(req.params.get("mname"))
            if mtype:
                mtype.setAccess("read", "")
                for key in req.params.keys():
                    if key.startswith("left"):
                        mtype.setAccess(key[4:], req.params.get(key).replace(";", ","))
                        break

    elif req.params.get("acttype") == "field":
        # section for fields
        for key in req.params.keys():
            # create new meta field
            if key.startswith("newdetail_"):
                return FieldDetail(req, req.params.get("parent"), "")

            # edit meta field
            elif key.startswith("editdetail_"):
                return FieldDetail(req, req.params.get("parent"), key[11:-2])

            # delete metafield: key[13:-2] = pid | n
            elif key.startswith("deletedetail_"):
                deleteMetaField(req.params.get("parent"), key[13:-2])
                return showDetailList(req, req.params.get("parent"))

            # change field order up
            if key.startswith("updetail_"):
                moveMetaField(req.params.get("parent"), key[9:-2], -1)
                return showDetailList(req, req.params.get("parent"))

            # change field order down
            elif key.startswith("downdetail_"):
                moveMetaField(req.params.get("parent"), key[11:-2], 1)
                return showDetailList(req, req.params.get("parent"))

        if "form_op" in req.params.keys():
            if req.params.get("form_op", "") == "cancel":
                return showDetailList(req, req.params.get("parent"))

            if existMetaField(req.params.get("parent"), req.params.get("mname")) and req.params.get("form_op", "") == "save_newdetail":
                return FieldDetail(req, req.params.get("parent"), req.params.get("orig_name", ""), 3)  # field still existing
            elif req.params.get("mname", "") == "" or req.params.get("mlabel", "") == "":
                return FieldDetail(req, req.params.get("parent"), req.params.get("orig_name", ""), 1)
            elif not checkString(req.params.get("mname", "")):
                # if the name contains wrong characters
                return FieldDetail(req, req.params.get("parent"), req.params.get("orig_name", ""), 4)

            _option = ""
            for o in req.params.keys():
                if o.startswith("option_"):
                    _option += o[7]

            _fieldvalue = ""
            if req.params.get("mtype", "") + "_value" in req.params.keys():
                _fieldvalue = str(req.params.get(req.params.get("mtype") + "_value"))

            _filenode = None
            if "valuesfile" in req.params.keys():
                valuesfile = req.params.pop("valuesfile")
                _filenode = importFileToRealname(valuesfile.filename, valuesfile.tempname)

            _attr_dict = {}
            if req.params.get("mtype", "") + "_handle_attrs" in req.params.keys():

                attr_names = [s.strip() for s in req.params.get(req.params.get("mtype", "") + "_handle_attrs").split(",")]
                key_prefix = req.params.get("mtype", "") + "_attr_"

                for attr_name in attr_names:
                    attr_value = req.params.get(key_prefix + attr_name, "")
                    _attr_dict[attr_name] = attr_value

            updateMetaField(req.params.get("parent", ""), req.params.get("mname", ""),
                            req.params.get("mlabel", ""), req.params.get("orderpos", ""),
                            req.params.get("mtype", ""), _option, req.params.get("mdescription", ""),
                            _fieldvalue, fieldid=req.params.get("fieldid", ""),
                            filenode=_filenode,
                            attr_dict=_attr_dict)

        return showDetailList(req, req.params.get("parent"))

    elif req.params.get("acttype") == "mask":

        # mask may have been edited: flush masks cache
        flush_maskcache(req=req)

        # section for masks
        for key in req.params.keys():

            # new mask
            if key.startswith("newmask_"):
                return MaskDetails(req, req.params.get("parent"), "")

            # edit metatype masks
            elif key.startswith("editmask_"):
                return MaskDetails(req, req.params.get("parent"), key[9:-2], err=0)

            # delete mask
            elif key.startswith("deletemask_"):
                mtype = getMetaType(req.params.get("parent"))
                mtype.removeChild(tree.getNode(key[11:-2]))
                return showMaskList(req, req.params.get("parent"))

            # create autmatic mask with all fields
            elif key.startswith("automask_"):
                generateMask(getMetaType(req.params.get("parent")))
                return showMaskList(req, req.params.get("parent"))

            # cope selected mask
            if key.startswith("copymask_"):
                mtype = getMetaType(req.params.get("parent"))
                mask = mtype.getMask(key[9:-2])
                cloneMask(mask, "copy_" + mask.getName())
                return showMaskList(req, req.params.get("parent"))

        if "form_op" in req.params.keys():
            if req.params.get("form_op", "") == "cancel":
                return showMaskList(req, req.params.get("parent"))

            if req.params.get("mname", "") == "":
                return MaskDetails(req, req.params.get("parent", ""), req.params.get("morig_name", ""), err=1)
            elif not checkString(req.params.get("mname", "")):
                # if the name contains wrong characters
                return MaskDetails(req, req.params.get("parent", ""), req.params.get("morig_name", ""), err=4)

            mtype = getMetaType(req.params.get("parent", ""))
            if req.params.get("form_op") == "save_editmask":
                mask = mtype.getMask(req.params.get("maskid", ""))

            elif req.params.get("form_op") == "save_newmask":
                mask = tree.Node(req.params.get("mname", ""), type="mask")
                mtype.addChild(mask)

            mask.setName(req.params.get("mname"))
            mask.setDescription(req.params.get("mdescription"))
            mask.setMasktype(req.params.get("mtype"))
            mask.setSeparator(req.params.get("mseparator"))

            if req.params.get("mtype") == "export":
                mask.setExportMapping(req.params.get("exportmapping") or "")
                mask.setExportHeader(req.params.get("exportheader"))
                mask.setExportFooter(req.params.get("exportfooter"))
                _opt = ""
                if "types" in req.params.keys():
                    _opt += "t"
                if "notlast" in req.params.keys():
                    _opt += "l"
                mask.setExportOptions(_opt)

            mask.setLanguage(req.params.get("mlanguage", ""))
            mask.setDefaultMask("mdefault" in req.params.keys())
            mask.setAccess("read", "")
            for key in req.params.keys():
                if key.startswith("left"):
                    mask.setAccess(key[4:], req.params.get(key).replace(";", ","))
                    break
        return showMaskList(req, str(req.params.get("parent", "")))
    return view(req)


""" show all defined metadatatypes """


def view(req):
    mtypes = loadTypesFromDB()
    actfilter = getFilter(req)

    # filter
    if actfilter != "":
        if actfilter in ("all", "*", t(lang(req), "admin_filter_all")):
            None  # all users
        elif actfilter == "0-9":
            num = re.compile(r'([0-9])')
            if req.params.get("filtertype", "") == "id":
                mtypes = filter(lambda x: num.match(x.getName()), mtypes)
            else:
                mtypes = filter(lambda x: num.match(x.getLongName()), mtypes)
        elif actfilter == "else" or actfilter == t(lang(req), "admin_filter_else"):
            all = re.compile(r'([a-z]|[A-Z]|[0-9]|\.)')
            if req.params.get("filtertype", "") == "id":
                mtypes = filter(lambda x: not all.match(x.getName()), mtypes)
            else:
                mtypes = filter(lambda x: not all.match(x.getLongName()), mtypes)
        else:
            if req.params.get("filtertype", "") == "id":
                mtypes = filter(lambda x: x.getName().lower().startswith(actfilter), mtypes)
            else:
                mtypes = filter(lambda x: x.getLongName().lower().startswith(actfilter), mtypes)

    pages = Overview(req, mtypes)
    order = getSortCol(req)

    # sorting
    if order != "":
        if int(order[0:1]) == 0:
            mtypes.sort(lambda x, y: cmp(x.getName().lower(), y.getName().lower()))
        elif int(order[0:1]) == 1:
            mtypes.sort(lambda x, y: cmp(x.getLongName().lower(), y.getLongName().lower()))
        elif int(order[0:1]) == 2:
            mtypes.sort(lambda x, y: cmp(x.getDescription().lower(), y.getDescription().lower()))
        elif int(order[0:1]) == 3:
            mtypes.sort(lambda x, y: cmp(x.getActive(), y.getActive()))
        elif int(order[0:1]) == 4:
            mtypes.sort(lambda x, y: cmp(x.getDatatypeString().lower(), y.getDatatypeString().lower()))
        elif int(order[0:1]) == 5:
            mtypes.sort(lambda x, y: cmp(x.metadatatype.getAccess("read"), y.metadatatype.getAccess("read")))
        elif int(order[0:1]) == 6:
            mtypes.sort(lambda x, y: cmp(x.searchIndexCorrupt(), y.searchIndexCorrupt()))
        elif int(order[0:1]) == 7:
            mtypes.sort(lambda x, y: cmp(len(x.getAllItems()), len(y.getAllItems())))
        if int(order[1:]) == 1:
            mtypes.reverse()
    else:
        mtypes.sort(lambda x, y: cmp(x.getName().lower(), y.getName().lower()))

    v = getAdminStdVars(req)
    v["sortcol"] = pages.OrderColHeader(
        [
            t(
                lang(req), "admin_meta_col_1"), t(
                lang(req), "admin_meta_col_2"), t(
                    lang(req), "admin_meta_col_3"), t(
                        lang(req), "admin_meta_col_4"), t(
                            lang(req), "admin_meta_col_5"), t(
                                lang(req), "admin_meta_col_6")])
    v["metadatatypes"] = mtypes
    v["datatypes"] = loadAllDatatypes()
    v["datatypes"].sort(lambda x, y: cmp(t(lang(req), x.getLongName()), t(lang(req), y.getLongName())))
    v["pages"] = pages
    v["actfilter"] = actfilter
    v["filterattrs"] = [("id", "admin_metatype_filter_id"), ("name", "admin_metatype_filter_name")]
    v["filterarg"] = req.params.get("filtertype", "id")
    return req.getTAL("web/admin/modules/metatype.html", v, macro="view_type")


""" form for metadata (edit/new) """


def MetatypeDetail(req, id, err=0):
    v = getAdminStdVars(req)

    if err == 0 and id == "":
        # new metadatatype
        metadatatype = tree.Node("", type="metadatatype")
        v["original_name"] = ""

    elif id != "" and err == 0:
        # edit metadatatype
        metadatatype = getMetaType(id)
        v["original_name"] = metadatatype.getName()

    else:
        # error
        metadatatype = tree.Node(req.params["mname"], type="metadatatype")
        metadatatype.setDescription(req.params["description"])
        metadatatype.setLongName(req.params["mlongname"])
        metadatatype.setActive("mactive" in req.params)
        metadatatype.setDatatypeString(req.params.get("mdatatypes", "").replace(";", ", "))
        metadatatype.set("bibtexmapping", req.params.get("mbibtex", ""))
        metadatatype.set("citeprocmapping", req.params.get("mciteproc", ""))

        v["original_name"] = req.params["mname_orig"]

    v["datatypes"] = loadNonSystemTypes()
    v["datatypes"].sort(lambda x, y: cmp(t(lang(req), x.getLongName()), t(lang(req), y.getLongName())))
    v["metadatatype"] = metadatatype
    v["error"] = err
    v["bibtextypes"] = getAllBibTeXTypes()
    v["bibtexselected"] = metadatatype.get("bibtexmapping").split(";")
    v["citeproctypes"] = citeproc.TYPES
    v["citeprocselected"] = metadatatype.get("citeprocmapping").split(";")

    rule = metadatatype.getAccess("read")
    if rule:
        rule = rule.split(",")
    else:
        rule = []

    rights = removeEmptyStrings(rule)
    v["acl"] = makeList(req, "read", rights, {}, overload=0, type="read")
    v["filtertype"] = req.params.get("filtertype", "")
    v["actpage"] = req.params.get("actpage")
    return req.getTAL("web/admin/modules/metatype.html", v, macro="modify_type")


""" popup info form """


def showInfo(req):
    return req.getTAL("web/admin/modules/metatype.html", {"fieldtypes": getMetaFieldTypeNames()}, macro="show_info")

""" popup form with field definition """


def showFieldOverview(req):
    path = req.path[1:].split("/")
    fields = getFieldsForMeta(path[1])
    fields.sort(lambda x, y: cmp(x.getOrderPos(), y.getOrderPos()))

    v = {}
    v["metadatatype"] = getMetaType(path[1])
    v["metafields"] = fields
    v["fieldoptions"] = fieldoption
    v["fieldtypes"] = getMetaFieldTypeNames()

    return req.getTAL("web/admin/modules/metatype.html", v, macro="show_fieldoverview")

""" export metadatatype-definition (XML) """


def export(req, name):
    return exportMetaScheme(name)

""" import definition from file """


def xmlimport(req, filename):
    importMetaSchema(filename)


def showEditor(req):
    path = req.path[1:].split("/")
    mtype = getMetaType(path[1])
    editor = mtype.getMask(path[2])

    req.params["metadatatype"] = mtype
    for key in req.params.keys():
        if req.params.get("op", "") == "cancel":
            if "savedetail" in req.params.keys():
                del req.params["savedetail"]
            break

        if key.startswith("up_"):
            changeOrder(tree.getNode(key[3:-2]).getParents()[0], tree.getNode(key[3:-2]).getOrderPos(), -1)
            break

        if key.startswith("down_"):
            changeOrder(tree.getNode(key[5:-2]).getParents()[0], -1, tree.getNode(key[5:-2]).getOrderPos())
            break

        if key.startswith("delete_"):
            editor.deleteMaskitem(key[7:-2])
            break

        if key.startswith("edit_"):
            op = key[5:-2]
            req.params["edit"] = op
            req.params["op"] = "edit"
            break

        if key.startswith("new_"):
            req.params["edit"] = " "
            break

        if key.startswith("newdetail_"):
            req.params["pid"] = key[10:-2]
            req.params["op"] = "newdetail"
            req.params["edit"] = " "
            if req.params.get("type")in("vgroup", "hgroup"):
                req.params["type"] = "field"
                req.params["op"] = "new"
            if "savedetail" in req.params.keys():
                del req.params["savedetail"]
            break

    if req.params.get("op", "") == "group":
        # create new group for selected objects
        req.params["op"] = "new"
        req.params["edit"] = " "
        req.params["type"] = req.params.get("group_type")
        req.params["pid"] = getNode(req.params.get("sel_id").split(";")[0]).getParents()[0].id

    if "saveedit" in req.params.keys() and req.params.get("op", "") != "cancel":
        # update node
        label = req.params.get("label", "-new-")
        if req.params.get("op", "") == "edit":
            item = tree.getNode(req.params.get("id"))
            item.setLabel(req.params.get("label", ""))

            if "mappingfield" in req.params.keys():
                # field of export mask
                item.set("attribute", req.params.get("attribute"))
                item.set("fieldtype", req.params.get("fieldtype"))
                mf = req.params.get("mappingfield").split(";")
                if req.params.get("fieldtype") == "mapping":  # mapping field of mapping definition selected
                    item.set("mappingfield", mf[0])
                else:  # attribute name as object name
                    item.set("mappingfield", ";".join(mf[1:]))
            else:
                f = tree.getNode(long(req.params.get("field")))

            field = item.getChildren()
            try:
                field = list(field)[0]
                if str(field.id) != str(req.params.get("field")):
                    item.removeChild(field)
                    item.addChild(f)
                field.setValues(req.params.get(field.get("type") + "_value", ""))
            except:
                pass

        elif req.params.get("op", "") == "new":
            if req.params.get("fieldtype", "") == "common":
                # existing field used
                fieldid = long(req.params.get("field"))
            elif "mappingfield" in req.params.keys():
                # new mapping field
                fieldid = ""  # long(req.params.get("mappingfield"))
                label = "mapping"

            else:
                # create new metaattribute
                parent = req.params.get("metadatatype").getName()
                fieldvalue = req.params.get(req.params.get("newfieldtype", "") + '_value', "")

                if req.params.get("type") == "label":
                    # new label
                    fieldid = ""
                else:
                    # normal field
                    updateMetaField(parent, req.params.get("fieldname"), label, 0,
                                    req.params.get("newfieldtype"), option="", description=req.params.get("description", ""),
                                    fieldvalues=fieldvalue, fieldvaluenum="", fieldid="")
                    fieldid = str(getMetaField(parent, req.params.get("fieldname")).id)

            item = editor.addMaskitem(label, req.params.get("type"), fieldid, req.params.get("pid", "0"))

            if "mappingfield" in req.params.keys():
                item.set("attribute", req.params.get("attribute"))
                item.set("fieldtype", req.params.get("fieldtype"))
                mf = req.params.get("mappingfield").split(";")
                if req.params.get("fieldtype") == "mapping":  # mapping field of mapping definition selected
                    item.set("mappingfield", mf[0])
                else:  # attribute name as object name
                    item.set("mappingfield", ";".join(mf[1:]))

            position = req.params.get("insertposition", "end")
            if position == "end":
                # insert at the end of existing mask
                item.setOrderPos(len(tree.getNode(req.params.get("pid")).getChildren()) - 1)
            else:
                # insert at special position
                fields = editor.getMaskFields()
                fields.sort(lambda x, y: cmp(x.getOrderPos(), y.getOrderPos()))
                for f in fields:
                    if f.getOrderPos() >= tree.getNode(position).getOrderPos() and f.id != item.id:
                        f.setOrderPos(f.getOrderPos() + 1)
                item.setOrderPos(tree.getNode(position).getOrderPos() - 1)

        item.setWidth(int(req.params.get("width", 400)))
        item.setUnit(req.params.get("unit", ""))
        item.setDefault(req.params.get("default", ""))
        item.setFormat(req.params.get("format", ""))
        item.setSeparator(req.params.get("separator", ""))
        item.setDescription(req.params.get("description", ""))
        item.setTestNodes(req.params.get("testnodes", ""))
        item.setMultilang(req.params.get("multilang", ""))

        if "required" in req.params.keys():
            item.setRequired(1)
        else:
            item.setRequired(0)

    if "savedetail" in req.params.keys():
        label = req.params.get("label", "-new-")
        # save details (used for hgroup)
        if req.params.get("op", "") == "edit":
            item = tree.getNode(req.params.get("id"))
            item.setLabel(req.params.get("label", ""))
        elif req.params.get("op", "") == "new":
            if req.params.get("sel_id", "") != "":
                item = editor.addMaskitem(label, req.params.get("type"), req.params.get(
                    "sel_id", "")[:-1], long(req.params.get("pid", "0")))
            else:
                item = editor.addMaskitem(label, req.params.get("type"), 0, long(req.params.get("pid", "0")))

        # move selected elementd to new item-container
        if req.params.get("sel_id", "") != "":
            pos = 0
            for i in req.params.get("sel_id")[:-1].split(";"):
                n = getNode(i)  # node to move
                n.setOrderPos(pos)
                p = getNode(n.getParents()[0].id)  # parentnode
                p.removeChild(n)
                item.addChild(n)  # new group
                pos += 1

        # position:
        position = req.params.get("insertposition", "end")
        if position == "end":
            # insert at the end of existing mask
            item.setOrderPos(len(tree.getNode(req.params.get("pid")).getChildren()) - 1)
        else:
            # insert at special position
            fields = []
            pidnode = getNode(req.params.get("pid"))
            for field in pidnode.getChildren():
                if field.getType().getName() == "maskitem" and field.id != pidnode.id:
                    fields.append(field)
            fields.sort(lambda x, y: cmp(x.getOrderPos(), y.getOrderPos()))
            for f in fields:
                if f.getOrderPos() >= tree.getNode(position).getOrderPos() and f.id != item.id:
                    f.setOrderPos(f.getOrderPos() + 1)
            item.setOrderPos(tree.getNode(position).getOrderPos() - 1)

        if "edit" not in req.params.keys():
            item.set("type", req.params.get("type", ""))
        item.setWidth(int(req.params.get("width", 400)))
        item.setUnit(req.params.get("unit", ""))
        item.setDefault(req.params.get("default", ""))
        item.setFormat(req.params.get("format", ""))
        item.setSeparator(req.params.get("separator", ""))
        item.setDescription(req.params.get("description", ""))
        if "required" in req.params.keys():
            item.setRequired(1)
        else:
            item.setRequired(0)

    v = {}
    v["edit"] = req.params.get("edit", "")
    if req.params.get("edit", "") != "":
        v["editor"] = editor.editItem(req)
    else:
        # show metaEditor
        v["editor"] = ""
        try:
            v["editor"] = req.getTALstr(editor.getMetaMask(language=lang(req)), {})
        except:
            v["editor"] = editor.getMetaMask(language=lang(req))

    v["title"] = editor.name

    return req.getTAL("web/admin/modules/metatype.html", v, macro="editor_popup")


def changeOrder(parent, up, down):
    """ change order of given nodes """
    i = 0
    for child in parent.getChildren().sort_by_orderpos():
        try:
            if i == up:
                pos = i - 1
            elif i == up - 1:
                pos = up
            elif i == down:
                pos = i + 1
            elif i == down + 1:
                pos = down
            else:
                pos = i
            child.setOrderPos(pos)
            i = i + 1
        except:
            pass
