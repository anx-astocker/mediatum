from core import config
from core.transition import httpstatus

from web.repec import RDFContent, HTTPContent, CollectionMixin
from web.repec.redif import redif_encode_archive, redif_encode_series


class HTMLCollectionContent(HTTPContent, CollectionMixin):
    """
    Base class for collection HTML content.
    """

    def __init__(self, req, status_code):
        super(HTMLCollectionContent, self).__init__(req)

        self.status_code = status_code

    def status(self):
        return self.status_code


class RDFCollectionContent(RDFContent, CollectionMixin):
    """
    Base class for collection RDF content.
    """

    def __init__(self, req, status_code):
        super(RDFCollectionContent, self).__init__(req)

        self.status_code = status_code

    def status(self):
        return self.status_code


class CollectionArchiveContent(RDFCollectionContent):
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
        collection_owner = self._get_node_owner(collection_node)
        root_domain = config.get("host.name", "mediatum.local")

        collection_data = {
            "Handle": "RePEc:%s" % collection_node["repec_code"],
            "URL": "http://%s/repec/%s" % (root_domain, collection_node["repec_code"]),
            "Name": collection_node.unicode_name,
            "Maintainer-Name": "Unknown",
            "Maintainer-Email": "nomail@%s" % root_domain,
            "Restriction": None,
        }

        if collection_owner:
            collection_data.update({
                "Maintainer-Name": collection_owner.unicode_name,
                "Maintainer-Email": collection_owner["email"],
            })

        return redif_encode_archive(collection_data)


class CollectionSeriesContent(RDFCollectionContent):
    """
    Class used for generating RDF of an series.
    """

    def __init__(self, req):
        super(CollectionSeriesContent, self).__init__(req, httpstatus.HTTP_INTERNAL_SERVER_ERROR)

        self.root_collection = self._get_root_collection()
        self.active_collection = self._get_active_collection()

    def rdf(self):
        if self.status_code != httpstatus.HTTP_OK:
            return ""

        collection_node = self.active_collection.node
        collection_owner = self._get_node_owner(collection_node)
        root_domain = config.get("host.name", "mediatum.local")

        collection_data = {
            "Name": "Working Papers",
            "Provider-Name": "Grandiose University, Department of Economics",
            "Provider-Homepage": "http://%s/" % root_domain,
            "Provider-Institution": "RePEc:edi:degraus",
            "Maintainer-Name": "Unknown",
            "Maintainer-Email": "nomail@%s" % root_domain,
            "Type": "ReDIF-Paper",
            "Handle": "RePEc:%s:wpaper" % collection_node["repec_code"],
        }

        if collection_owner:
            collection_data.update({
                "Maintainer-Name": collection_owner.unicode_name,
                "Maintainer-Email": collection_owner["email"],
            })

        return redif_encode_series(collection_data)
