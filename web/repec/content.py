from core import tree
from core.acl import AccessData
from core.transition import httpstatus

from web.repec import RDFContent
from web.repec.redif import redif_encode_archive


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

    def __init__(self, req):
        super(CollectionContent, self).__init__(req)

        self.archive_code = "aaa"  # TODO: archive code from collection
        self.status_code = httpstatus.HTTP_INTERNAL_SERVER_ERROR
        self.root_collection = self._get_root_collection()
        self.active_collection = self._get_active_collection()

    def status(self):
        return self.status_code

    def rdf(self):
        # TODO: use real data
        return redif_encode_archive({
            "Handle": "RePEc:%s" % self.archive_code,
            "URL": "http://www.test.at/",
            "Maintainer-Email": "test@test.at",
            "Name": "Das ist ein Test",
            "Maintainer-Name": "Max Muster",
            "Maintainer-Phone": "+43 1234 567890",
            "Maintainer-Fax": "+43 1234 567890 123",
            "Homepage": "http://www.test.at/",
            "Description": "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor "
                           "invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et "
                           "accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata "
                           "sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing "
                           "elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, "
                           "sed diam voluptua.",
            "Notification": "Test",
            "Restriction": None,
        })

    def _get_root_collection(self):
        return NodeContent(self.request, self, tree.getRoot("collections"))

    def _get_active_collection(self):
        acl = AccessData(self.request)
        collection_id = self.request.params.get("id", self.root_collection.node.id)

        # try to load the node
        try:
            node = tree.getNode(collection_id)
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