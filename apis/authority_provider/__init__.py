from flask import abort
from flask import request
from flask_restplus import Resource
from flask_restplus import Namespace
from flask_restplus import reqparse
from elasticsearch import Elasticsearch

from apis import output
from apis.helper_functions import get_authorities
from apis.helper_functions import get_indices
from apis.helper_functions import load_config

api = Namespace(name="authority_search", path="/", description="Authority Provider Identifier Search")

@api.route('/<any({}):authority_provider>/<string:id>'.format(str(get_authorities())),methods=['GET'])
@api.param('authority_provider','The name of the authority-provider to access. Allowed Values: {}.'.format(str(get_authorities())))
@api.param('id','The ID-String of the authority-identifier to access. Possible Values (examples): 208922695, 118695940, 20474817, Q1585819')

class AutSearch(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('format',type=str,help="set the Content-Type over this Query-Parameter. Allowed: nt, rdf, ttl, nq, jsonl, json",location="args")
    parser.add_argument('size',type=int,help="Configure the maxmimum amount of hits to be returned",location="args",default=100)
    parser.add_argument('from',type=int,help="Configure the offset from the frist result you want to fetch",location="args",default=0)
    es_host, es_port, excludes, indices, authorities =load_config("apiconfig.json", "es_host","es_port","excludes","indices","authorities")
    es=Elasticsearch([{'host':es_host}],port=es_port,timeout=10)

    @api.response(200,'Success')
    @api.response(404,'Record(s) not found')
    @api.expect(parser)
    @api.doc('get record by authority-id')
    def get(self,authority_provider,id):
        """
        search for an given ID of a given authority-provider
        """
        print(type(self).__name__)
        retarray=[]
        args=self.parser.parse_args()
        name=""
        ending=""
        if "." in id:
            dot_fields=id.split(".")
            name=dot_fields[0]
            ending=dot_fields[1]
        else:
            name=id
            ending=""
        if not authority_provider in self.authorities:
            abort(404)
        search={"_source":{"excludes":self.excludes},"query":{"query_string" : {"query":"sameAs.keyword:\""+self.authorities.get(authority_provider)+name+"\""}}}    
        res=self.es.search(index=','.join(get_indices()[:-1]),body=search,size=args.get("size"),from_=args.get("from"),_source_exclude=self.excludes)
        if "hits" in res and "hits" in res["hits"]:
            for hit in res["hits"]["hits"]:
                retarray.append(hit.get("_source"))
        return output.parse(retarray,args.get("format"),ending,request)

@api.route('/<any({aut}):authority_provider>/<any({ent}):entity_type>/<string:id>'.format(aut=str(get_authorities()),ent=get_indices()),methods=['GET'])
@api.param('authority_provider','The name of the authority-provider to access. Allowed Values: {}.'.format(str(get_authorities())))
@api.param('entity_type','The name of the entity-index to access. Allowed Values: {}.'.format(get_indices()))
@api.param('id','The ID-String of the authority-identifier to access. Possible Values (examples): 208922695, 118695940, 20474817, Q1585819')
class AutEntSearch(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('format',type=str,help="set the Content-Type over this Query-Parameter. Allowed: nt, rdf, ttl, nq, jsonl, json",location="args")
    parser.add_argument('size',type=int,help="Configure the maxmimum amount of hits to be returned",location="args",default=100)
    parser.add_argument('from',type=int,help="Configure the offset from the frist result you want to fetch",location="args",default=0)
    es_host, es_port, excludes, indices, authorities = load_config("apiconfig.json", "es_host","es_port","excludes","indices","authorities")
    es=Elasticsearch([{'host':es_host}],port=es_port,timeout=10)

    @api.response(200,'Success')
    @api.response(404,'Record(s) not found')
    @api.expect(parser)
    @api.doc('get record by authority-id and entity-id')
    def get(self,authority_provider,entity_type,id):
        """
        search for an given ID of a given authority-provider on a given entity-index
        """
        print(type(self).__name__)
        retarray=[]
        args=self.parser.parse_args()
        name=""
        ending=""
        if "." in id:
            dot_fields=id.split(".")
            name=dot_fields[0]
            ending=dot_fields[1]
        else:
            name=id
            ending=""
        if not authority_provider in self.authorities or entity_type not in get_indices():
            abort(404)
        search={"_source":{"excludes":self.excludes},"query":{"query_string" : {"query":"sameAs.keyword:\""+self.authorities.get(authority_provider)+name+"\""}}}    
        res=self.es.search(index=entity_type,body=search,size=args.get("size"),from_=args.get("from"),_source_exclude=self.excludes)
        if "hits" in res and "hits" in res["hits"]:
            for hit in res["hits"]["hits"]:
                retarray.append(hit.get("_source"))
        return output.parse(retarray, args.get("format"), ending, request) 