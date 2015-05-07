from core.transition import httpstatus


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