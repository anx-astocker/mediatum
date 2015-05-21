import logging

from mediatumtal import tal

from core import config
from core.transition import httpstatus

from web.repec import RDFContent, HTMLContent, CollectionMixin, Node
from web.repec.redif import *


log = logging.getLogger("repec")


class HTMLCollectionContent(HTMLContent, CollectionMixin):
    """
    Lists the content of the RePEc collection as HTML.
    """

    def __init__(self, req):
        super(HTMLCollectionContent, self).__init__(req)

        self.status_code = httpstatus.HTTP_OK

    def status(self):
        return self.status_code

    def html(self):
        return tal.processTAL({
            "items": [
                ("./aaaarch.rdf", "aaaarch.rdf"),
                ("./aaaseri.rdf", "aaaseri.rdf"),
                ("./journl/", "journl"),
                ("./wpaper/", "wpaper"),
            ]
        }, file="web/repec/templates/directory_browsing.html", request=self.request)


class HTMLCollectionPaperContent(HTMLContent, CollectionMixin):
    """
    Lists the content of the RePEc working papers as HTML.
    """

    def __init__(self, req):
        super(HTMLCollectionPaperContent, self).__init__(req)

        self.status_code = httpstatus.HTTP_OK

    def status(self):
        return self.status_code

    def html(self):
        return tal.processTAL({
            "items": [
                ("./papers.rdf", "papers.rdf"),
            ]
        }, file="web/repec/templates/directory_browsing.html", request=self.request)


class HTMLCollectionJournalContent(HTMLContent, CollectionMixin):
    """
    Lists the content of the RePEc journal as HTML.
    """

    def __init__(self, req):
        super(HTMLCollectionJournalContent, self).__init__(req)

        self.status_code = httpstatus.HTTP_OK

    def status(self):
        return self.status_code

    def html(self):
        return tal.processTAL({
            "items": [
                ("./journals.rdf", "journals.rdf"),
            ]
        }, file="web/repec/templates/directory_browsing.html", request=self.request)


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
        root_domain = config.get("host.name")

        collection_data = {
            "Handle": "RePEc:%s" % collection_node["repec.code"],
            "URL": "%s/repec/%s" % (self._get_root_url(), collection_node["repec.code"]),
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
    Class used for generating RDF of a series.
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
        root_domain = config.get("host.name")

        repec_code = collection_node["repec.code"]
        provider_name = self._get_inherited_attribute_value(collection_node, "tuminstid")
        provider_id = str(provider_name).lower()

        collection_data = {
            "Name": "Working Papers",
            "Provider-Name": "TUM, %s" % provider_name,
            "Provider-Institution": "RePEc:%s:%s" % (repec_code, provider_id),
            "Maintainer-Name": "Unknown",
            "Maintainer-Email": "nomail@%s" % root_domain,
            "Type": "ReDIF-Paper",
            "Handle": "RePEc:%s:wpaper" % repec_code,
        }

        if collection_owner:
            collection_data.update({
                "Maintainer-Name": collection_owner.unicode_name,
                "Maintainer-Email": collection_owner["email"],
            })

        wpaper_series_rdf = redif_encode_series(collection_data)

        collection_data = {
            "Name": "Journal",
            "Provider-Name": "TUM, %s" % provider_name,
            "Provider-Institution": "RePEc:%s:%s" % (repec_code, provider_id),
            "Maintainer-Name": "Unknown",
            "Maintainer-Email": "nomail@%s" % root_domain,
            "Type": "ReDIF-Article",
            "Handle": "RePEc:%s:journl" % repec_code,
        }

        if collection_owner:
            collection_data.update({
                "Maintainer-Name": collection_owner.unicode_name,
                "Maintainer-Email": collection_owner["email"],
            })

        journl_series_rdf = redif_encode_series(collection_data)

        return "\n\n".join((wpaper_series_rdf, journl_series_rdf))


class CollectionJournalContent(RDFCollectionContent):
    """
    Class used for generating RDF of working papers.
    """

    def __init__(self, req):
        super(CollectionJournalContent, self).__init__(req, httpstatus.HTTP_INTERNAL_SERVER_ERROR)

        self.root_collection = self._get_root_collection()
        self.active_collection = self._get_active_collection()

    def rdf(self):
        if self.status_code != httpstatus.HTTP_OK:
            return ""

        child_nodes = self.active_collection.get_all_child_nodes_by_field_value(**{"repec.type": "ReDIF-Article"})
        repec_code = self.active_collection.node["repec.code"]
        rdf_content = []

        for child_node in child_nodes:
            # skip file if mandatory fields are not present
            if None in (child_node.get("author.fullname"), child_node.get("title")):
                continue

            creation_date = Node._get_datetime_from_iso_8601(child_node.get("creationtime"))
            update_date = Node._get_datetime_from_iso_8601(child_node.get("updatetime"))
            file_url = self._get_document_pdf_url(child_node.node)

            file_data = {
                "_author_1": {
                    "Author-Name": child_node.get("author.fullname"),
                    "Author-Name-First": child_node.get("author.firstname"),
                    "Author-Name-Last": child_node.get("author.surname"),
                    "Author-Email": child_node.get("author.public_email"),
                    "Author-Workplace-Name": child_node.get("author.origin"),
                },
                "_file_1": {
                    "File-URL": file_url,
                    "File-Format": "application/pdf",
                    "File-Function": "%s, %s" % (child_node.get("type"), child_node.get("year")) \
                        if child_node.get("type") and child_node.get("year") else None,
                } if file_url else None,
                "Title": child_node.get("title"),
                "Pages": child_node.get("repec.article.pages"),
                "Volume": child_node.get("repec.article.volume"),
                "Issue": child_node.get("repec.article.issue"),
                "Classification-JEL": child_node.get("repec.classification"),
                "Number": child_node.node.id,
                "Year": child_node.get("year") if child_node.get("year") else None,
                "Keywords": child_node.get("keywords"),
                "Creation-Date": "%s-%s" % (creation_date.year, creation_date.month),
                "Revision-Date": "%s-%s" % (update_date.year, update_date.month),
                "Handle": "RePEc:%s:journl:%s" % (repec_code, child_node.node.id),
            }
            rdf_content.append(redif_encode_article(file_data))

        return "\n\n".join(rdf_content)


class CollectionPaperContent(RDFCollectionContent):
    """
    Class used for generating RDF of journals.
    """

    def __init__(self, req):
        super(CollectionPaperContent, self).__init__(req, httpstatus.HTTP_INTERNAL_SERVER_ERROR)

        self.root_collection = self._get_root_collection()
        self.active_collection = self._get_active_collection()

    def rdf(self):
        if self.status_code != httpstatus.HTTP_OK:
            return ""

        child_nodes = self.active_collection.get_all_child_nodes_by_field_value(**{"repec.type": "ReDIF-Paper"})
        repec_code = self.active_collection.node["repec.code"]
        rdf_content = []

        for child_node in child_nodes:
            # skip file if mandatory fields are not present
            if None in (child_node.get("author.fullname"), child_node.get("title")):
                continue

            creation_date = Node._get_datetime_from_iso_8601(child_node.get("creationtime"))
            update_date = Node._get_datetime_from_iso_8601(child_node.get("updatetime"))
            file_url = self._get_document_pdf_url(child_node.node)

            file_data = {
                "_author_1": {
                    "Author-Name": child_node.get("author.fullname"),
                    "Author-Name-First": child_node.get("author.firstname"),
                    "Author-Name-Last": child_node.get("author.surname"),
                    "Author-Email": child_node.get("author.public_email"),
                    "Author-Workplace-Name": child_node.get("author.origin"),
                },
                "_file_1": {
                    "File-URL": file_url,
                    "File-Format": "application/pdf",
                    "File-Function": "%s, %s" % (child_node.get("type"), child_node.get("year")) \
                        if child_node.get("type") and child_node.get("year") else None,
                } if file_url else None,
                "Title": child_node.get("title"),
                "Abstract": child_node.get("description"),
                "Length": "%s pages" % child_node.get("pdf_pages") if child_node.get("pdf_pages") else None,
                "Language": child_node.get("lang"),
                "Classification-JEL": child_node.get("repec.classification"),
                "Creation-Date": "%s-%s" % (creation_date.year, creation_date.month),
                "Revision-Date": "%s-%s" % (update_date.year, update_date.month),
                "Publication-Status": "Published by %s" % child_node.get("publisher") \
                    if child_node.get("publisher") else None,
                "Number": child_node.node.id,
                "Keywords": child_node.get("keywords"),
                "Handle": "RePEc:%s:wpaper:%s" % (repec_code, child_node.node.id),
            }
            rdf_content.append(redif_encode_paper(file_data))

        return "\n\n".join(rdf_content)
