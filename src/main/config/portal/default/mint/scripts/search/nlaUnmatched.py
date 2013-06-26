from com.googlecode.fascinator.common import JsonObject
from com.googlecode.fascinator.common import JsonSimple
from com.googlecode.fascinator.api.indexer import SearchRequest
from com.googlecode.fascinator.common.solr import SolrResult

from java.io import ByteArrayInputStream, ByteArrayOutputStream
from java.lang import Exception
from org.json.simple import JSONArray

class NlaUnmatchedData:
    def __init__(self):
        pass

    def __activate__(self, context):
        self.request = context["request"]
        self.response = context["response"]
        self.formData = context["formData"]
        self.services = context["Services"]
        self.log = context["log"]
        self.config   = context["systemConfig"]

        # Prepare response Object
        format = self.formData.get("format")
        if format == "json":
            out = self.response.getPrintWriter("application/json; charset=UTF-8")
        else:
            out = self.response.getPrintWriter("text/plain; charset=UTF-8")

        # Success Response
        try:
            out.println(self.__getSolrData())
        except Exception, ex:
            self.log.error("Error during search: ", ex)
            self.response.setStatus(500)
        out.close()

    def __getSolrData(self):
        query = "*:*"
        req = SearchRequest(query)
        req.setParam("fq", 'item_type:"object"')
        req.addParam("fq", "repository_type:\"Parties\"")
        req.addParam("fq", "repository_name:\"People\"")
        req.addParam("fq", "ready_for_nla:\"ready\"")
        req.addParam("fq", "-nlaId:[* TO *]")
        req.setParam("fl", "score")
        req.setParam("sort", "score desc, f_dc_title asc")
        req.setParam("start", "0")
        req.setParam("rows", "99999")
        
        try:
            out = ByteArrayOutputStream()
            indexer = self.services.getIndexer()
            indexer.search(req, out)
            return SolrResult(ByteArrayInputStream(out.toByteArray()))
        except Exception, e:
            self.log.error("Failed to lookup '{}': {}", prefix, e.getMessage())
        
        return SolrResult('{"response":{"numFound":0}}')
 
    def getResults(self):
        return self.__getSolrData().getResults()

