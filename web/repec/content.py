import re

from core import tree, config
from core.acl import AccessData
from core.users import getUser
from core.transition import httpstatus

from web.repec import RDFContent
from web.repec.redif import redif_encode_archive


_MATCH_REPEC_CODE = re.compile(r"^/repec/(?P<code>[\d\w]+)/((?P<code_check>[\d\w]+)(arch)|(seri))?.*$")


class NodeContent(RDFContent):

    def __init__(self, req, collection_content, node):
        super(NodeContent, self).__init__(req)

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

        return [NodeContent(self.request, self.collection_content, n) for n in nodes]


class CollectionContent(RDFContent):
    """
    Base class for collection RDF content.
    """

    def __init__(self, req, status_code):
        super(CollectionContent, self).__init__(req)

        self.status_code = status_code

    def status(self):
        return self.status_code

    def _get_root_collection(self):
        """
        Gets the root collection of the entire MediaTUM database.
        """
        return NodeContent(self.request, self, tree.getRoot("collections"))

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

        return NodeContent(self.request, self, node)


class CollectionArchiveContent(CollectionContent):
    """
    Class used for generating RDF of an archive.
    """

    def __init__(self, req):
        super(CollectionArchiveContent, self).__init__(req, httpstatus.HTTP_INTERNAL_SERVER_ERROR)

        self.root_collection = self._get_root_collection()
        self.active_collection = self._get_active_collection()

    def rdf(self):
        if self.status_code != httpstatus.HTTP_OK:
            return ""

        collection_node = self.active_collection.node
        collection_owner = getUser(collection_node["creator"])
        root_domain = config.get("host.name", "mediatum.local")

        # TODO: use real data
        return redif_encode_archive({
            "Handle": "RePEc:%s" % collection_node["repec_code"],
            "URL": "http://%s/repec/%s" % (root_domain, collection_node["repec_code"]),
            "Name": collection_node.unicode_name,
            "Maintainer-Name": collection_owner.unicode_name,
            "Maintainer-Email": collection_owner["email"],
            "Restriction": None,
        })
