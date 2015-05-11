import re

from core import tree
from core.acl import AccessData
from core.users import getUser
from core.transition import httpstatus

from web.repec.redif import redif_encode_archive, redif_encode_series


_MATCH_REPEC_CODE = re.compile(r"^/repec/(?P<code>[\d\w]+)/((?P<code_check>[\d\w]+)(arch)|(seri))?.*$")


class RDFContent(object):

    def __init__(self, req):
        self.request = req

    def rdf(self):
        return ""

    def status(self):
        return httpstatus.HTTP_OK

    def respond(self):
        self.request.write(self.rdf())
        return self.status()


class HTTPContent(object):

    def __init__(self, req):
        self.request = req

    def html(self):
        return ""

    def status(self):
        return httpstatus.HTTP_OK

    def respond(self):
        self.request.write(self.html())
        return self.status()


class CollectionMixin(object):

    def _get_inherited_attribute_value(self, node, attr):
        try:
            # try to get the attr from given node
            return node[attr]
        except KeyError:
            if node.id != 1:  # do not traverse up if we are on root node
                for parent in node.getParents():
                    try:
                        # go up in tree
                        return self._get_inherited_attribute_value(parent, attr)
                    except KeyError:
                        pass

        # attr does not exist in node tree
        raise KeyError

    def _get_node_owner(self, node):
        try:
            node_owner = getUser(node["creator"])
            if node_owner:
                return node_owner
        except KeyError:
            pass
        try:
            node_owner = getUser(node["updateuser"])
            if node_owner:
                return node_owner
        except KeyError:
            pass

        return None

    def _get_root_collection(self):
        """
        Gets the root collection of the entire MediaTUM database.
        """
        return Node(self.request, self, tree.getRoot("collections"))

    def _get_active_collection(self):
        """
        Gets the active collection based on the request url. The RePEc code is used to
        choose the collection. Expects URL path in the format as follows:

        * `/repec/REPEC_CODE`
        * `/repec/REPEC_CODE/REPEC_CODEarch.rdf`
        * `/repec/REPEC_CODE/REPEC_CODEseri.rdf`
        * `/repec/REPEC_CODE/journl/...`
        * `/repec/REPEC_CODE/wpaper/...`
        """
        acl = AccessData(self.request)

        try:
            path_match = _MATCH_REPEC_CODE.match(self.request.fullpath)
            repec_code = path_match.group("code")
            repec_code_check = path_match.group("code_check")

            # if we have a check-code in the url, it must equal the code value
            if repec_code_check is not None and repec_code_check != repec_code:
                raise AttributeError

        except (IndexError, AttributeError):
            # path does not contain a repec code
            self.status_code = httpstatus.HTTP_NOT_FOUND
            return None

        # try to load the node
        try:
            nodes = tree.getNodesByFieldValue(repec_code=repec_code)
            if len(nodes) != 1:
                raise tree.NoSuchNodeError
            node = nodes[0]
        except tree.NoSuchNodeError:
            # requested node not in DB, so set status to 404
            self.status_code = httpstatus.HTTP_NOT_FOUND
            return None

        if not acl.hasReadAccess(node):
            # requested node in DB but no access, so set status to 403
            self.status_code = httpstatus.HTTP_FORBIDDEN
            return None

        if node.type not in ("directory", "collection"):
            # requested node in DB and accessible, but not a collection type
            self.status_code = httpstatus.HTTP_INTERNAL_SERVER_ERROR
            return None

        # node exists and accessible
        self.status_code = httpstatus.HTTP_OK

        return Node(self.request, self, node)


class Node(RDFContent):

    def __init__(self, req, collection_content, node):
        super(Node, self).__init__(req)

        self.collection_content = collection_content
        self.node = node

    def get_all_files(self):
        return self.__get_files(lambda: tree.getAllContainerChildrenAbs(self.node, list()))

    def get_files(self):
        return self.__get_files(self.node.getContentChildren)

    def __get_files(self, fetch_function):
        acl = AccessData(self.request)

        node_ids = acl.filter(fetch_function())
        nodes = tree.NodeList(node_ids)

        return [Node(self.request, self.collection_content, n) for n in nodes]