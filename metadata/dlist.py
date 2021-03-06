"""
 mediatum - a multimedia content repository

 Copyright (C) 2011 Arne Seifert <seiferta@in.tum.de>
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
import urllib2
import json

from mediatumtal import tal
import core.tree as tree
from utils.utils import esc
from core.metatype import Metatype


class m_dlist(Metatype):

    def formatValues(self, context):
        valuelist = []

        items = {}
        try:
            n = context.collection
            if n is None:
                raise tree.NoSuchNodeError()
            items = n.getAllAttributeValues(context.field.getName(), context.access)
        except tree.NoSuchNodeError:
            None

        value = context.value.split(";")

        for val in context.field.getValueList():
            indent = 0
            canbeselected = 0
            while val.startswith("*"):
                val = val[1:]
                indent = indent + 1
            if val.startswith(" "):
                canbeselected = 1
            val = val.strip()
            if not indent:
                canbeselected = 1
            if indent > 0:
                indent = indent - 1
            indentstr = "&nbsp;" * (2 * indent)

            num = 0
            if val in items.keys():
                num = int(items[val])

            try:
                if int(num) < 0:
                    raise ""
                elif int(num) == 0:
                    num = ""
                else:
                    num = " (" + str(num) + ")"
            except:
                num = ""

            val = esc(val)

            if not canbeselected:
                valuelist.append(("optgroup", "<optgroup label=\"" + indentstr + val + "\">", "", ""))
            elif (val in value):
                valuelist.append(("optionselected", indentstr, val, num))
            else:
                valuelist.append(("option", indentstr, val, num))
        return valuelist

    def getEditorHTML(self, field, value="", width=400, name="", lock=0, language=None, required=None):
        fielddef = field.getValues().split("\r\n")  # url(source), type, name variable, value variable
        if name == "":
            name = field.getName()
        while len(fielddef) < 5:
            fielddef.append("")

        valuelist = []
        try:
            if fielddef[1] == 'json':
                opener = urllib2.build_opener()
                f = opener.open(urllib2.Request(fielddef[0], None, {}))
                data = json.load(f)
                data.sort(lambda x, y: cmp(x[fielddef[2]], y[fielddef[2]]))
                for item in data:
                    valuelist.append({'select_text': fielddef[4].replace(fielddef[2], item[fielddef[2]]).replace(
                        fielddef[3], item[fielddef[3]]), 'select_value': item[fielddef[3]]})
                f.close()
            elif fielddef[1] == 'list':
                opener = urllib2.build_opener()
                f = opener.open(urllib2.Request(fielddef[0], None, {}))
                for item in f.read().split("\n"):
                    if not item.startswith("#"):
                        if ";" in item:
                            _v, _t = item.split(";")
                        else:
                            _v = _t = item
                        valuelist.append({'select_text': _t.strip(), 'select_value': _v.strip()})
                f.close()
        except:
            #enables the field to be added without fields filled in without throwing an exception
            pass
        return tal.getTAL("metadata/dlist.html", {"lock": lock,
                                                   "name": name,
                                                   "width": width,
                                                   "value": value,
                                                   "valuelist": valuelist,
                                                   "fielddef": fielddef,
                                                   "required": self.is_required(required)},
                          macro="editorfield",
                          language=language)

    def getSearchHTML(self, context):
        return tal.getTAL("metadata/dlist.html",
                          {"context": context,
                           "valuelist": filter(lambda x: x != "",
                                               self.formatValues(context))},
                          macro="searchfield",
                          language=context.language)

    def getFormatedValue(self, field, node, language=None, html=1):
        value = node.get(field.getName())
        if html:
            value = esc(value)
        return (field.getLabel(), value)

    def getMaskEditorHTML(self, field, metadatatype=None, language=None):
        try:
            value = field.getValues().split("\r\n")
        except:
            value = []
        while len(value) < 5:
            value.append("")  # url(source), name variable, value variable
        return tal.getTAL("metadata/dlist.html", {"value": value, "types": ['json', 'list']}, macro="maskeditor", language=language)

    def getName(self):
        return "fieldtype_dlist"

    def getInformation(self):
        return {"moduleversion": "1.0", "softwareversion": "1.1"}

    # method for additional keys of type list
    def getLabels(self):
        return m_dlist.labels

    labels = {"de":
              [
                  ("dlist_list_values", "Dynamische Listenwerte:"),
                  ("fieldtype_dlist", "Dynamische Werteliste"),
                  ("fieldtype_dlist_desc", "Werte-Auswahlfeld als Drop-Down Liste"),
                  ("dlist_edit_source", "Adresse der Daten:"),
                  ("dlist_edit_type", "Typ der Daten:"),
                  ("dlist_edit_attr", "Attribut-Variable:"),
                  ("dlist_edit_valattr", "Werte-Variable:"),
                  ("dlist_type_json", "Json:"),
                  ("dlist_type_list", "Liste:"),
                  ("dlist_edit_format", "Anzeigeformat:")
              ],
              "en":
              [
                  ("dlist_list_values", "Dynamic List values:"),
                  ("fieldtype_dlist", "dynamic valuelist"),
                  ("fieldtype_dlist_desc", "drop down valuelist"),
                  ("dlist_edit_source", "address of data:"),
                  ("dlist_edit_type", "type of data:"),
                  ("dlist_edit_attr", "attribute variable:"),
                  ("dlist_edit_valattr", "value variable:"),
                  ("dlist_type_json", "Json:"),
                  ("dlist_type_list", "List:"),
                  ("dlist_edit_format", "format in selection:")
              ]
              }
