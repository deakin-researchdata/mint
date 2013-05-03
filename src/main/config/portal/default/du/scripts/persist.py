import os, re

from download import DownloadData

from com.googlecode.fascinator.api.indexer import SearchRequest
from com.googlecode.fascinator.api.storage import StorageException
from com.googlecode.fascinator.common import JsonSimple
from com.googlecode.fascinator.common.solr import SolrDoc, SolrResult

from java.io import ByteArrayInputStream, ByteArrayOutputStream
from java.lang import Boolean
from java.net import URLDecoder, URLEncoder

class PersistData:
    def __init__(self):
        pass

    def __activate__(self, context):
        self.services = context["Services"]
        self.request = context["request"]
        self.response = context["response"]

        uri = URLDecoder.decode(self.request.getAttribute("RequestURI"))
        matches = re.match("^(.*?)/(.*?)/(?:(.*?)/)?(.*)$", uri)
        if matches and matches.group(3):
            self.__oid = matches.group(3)

            self.__metadata = None
            self.__object = None
            self.__readMetadata()

            profile_page = self.__metadata.getFirst("Staff_Profile_Homepage")
            published = self.__metadata.getFirst("published")

            if profile_page :
                self.response.sendRedirect(profile_page)
            elif published == "true" :
                self.response.sendRedirect("%s%s/%s" % (context["urlBase"], "published/detail", self.__oid))
            else :
                self.response.sendRedirect("%s%s/%s" % (context["urlBase"], "default/detail", self.__oid))
        else:
            self.response.sendRedirect("%s%s/" % (context["urlBase"], uri ))


    def getObject(self):
        return self.__object

    def isIndexed(self):
        found = self.__solrData.getNumFound()
        return (found is not None) and (found == 1)

    def __getObject(self):
        self.__loadSolrData()

        if not self.isIndexed():
            print "WARNING: Object '%s' not found in index" % self.__oid
            sid = None
        else:
            # Query storage for this object
            sid = self.__solrData.getResults().get(0).getFirst("storage_id")

        try:
            if sid is None:
                # Use the URL OID
                object = self.services.getStorage().getObject(self.__oid)
            else:
                # We have a special storage ID from the index
                object = self.services.getStorage().getObject(sid)
        except StorageException, e:
            #print "Failed to access object: %s" % (str(e))
            return None

        return object

    def __loadSolrData(self):
        query = 'id:"%s"' % self.__oid
        req = SearchRequest(query)
        req.addParam("fq", 'item_type:"object"')
        out = ByteArrayOutputStream()
        self.services.getIndexer().search(req, out)
        self.__solrData = SolrResult(ByteArrayInputStream(out.toByteArray()))

    def __readMetadata(self):
        self.__loadSolrData()
        if self.isIndexed():
            self.__metadata = self.__solrData.getResults().get(0)
            if self.__object is None:
                # Try again, indexed records might have a special storage_id
                self.__object = self.__getObject()
        else:
            self.__metadata.getJsonObject().put("id", self.__oid)
