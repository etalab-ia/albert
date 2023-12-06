#!/bin/python
import sys
from pprint import pprint

sys.path.append(".")

from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client import models as QdrantModels

from api.app.config import (ELASTICSEARCH_CREDS, ELASTICSEARCH_IX_VER,
                            ELASTICSEARCH_URL, QDRANT_IX_VER, QDRANT_URL,
                            collate_ix_name)

# from api.app.core.embeddings import make_embeddings


def search(name, query, limit, similarity, institution, sources):
    if name == "experiences":
        retrieves = [
            "id_experience",
            "titre",
            "description",
            "intitule_typologie_1",
            "reponse_structure_1",
        ]
    elif name == "sheets" and similarity not in ["e5"]:
        retrieves = [
            "sid",
            "title",
            "url",
            "introduction",
            "theme",
            "surtitre",
            "source",
            "related_questions",
            "web_services",
        ]
    elif name == "chunks" or (similarity in ["e5"] and name == "sheets"):
        retrieves = [
            "hash",
            "title",
            "url",
            "introduction",
            "text",
            "context",
            "theme",
            "surtitre",
            "source",
            "related_questions",
            "web_services",
        ]
    else:
        raise NotImplementedError

    _extract = lambda x: dict((r, x[r]) for r in retrieves if r in x)

    hits = None
    if similarity == "bm25":
        client = Elasticsearch(ELASTICSEARCH_URL, basic_auth=ELASTICSEARCH_CREDS)
        query_filter = []
        if institution:
            query_filter.append({"term": {"intitule_typologie_1": institution}})
        if sources:
            query_filter.append({"terms": {"source": sources}})

        body = {
            "query": {
                "bool": {
                    "must": [{"multi_match": {"query": query, "fuzziness": "AUTO"}}],
                    "filter": query_filter,
                }
            },
            "size": limit,
        }
        res = client.search(index=collate_ix_name(name, ELASTICSEARCH_IX_VER), body=body)
        hits = [_extract(x.get("_source")) for x in res["hits"]["hits"] if x]

    elif similarity == "e5":
        do_unique_sheets = False
        if name == "sheets":
            name = "chunks"
            limit = limit * 5
            do_unique_sheets = True

        embeddings = make_embeddings(query)
        client = QdrantClient(url=QDRANT_URL, grpc_port=6334, prefer_grpc=True)
        # Eventually set filters
        query_filter = None
        if institution:
            query_filter = QdrantModels.Filter(
                must=[
                    QdrantModels.FieldCondition(
                        key="intitule_typologie_1",
                        match=QdrantModels.MatchValue(
                            value=institution,
                        ),
                    )
                ]
            )
        if sources:
            # @debug: institution and sources are two independant filters (one for experinces, the others for sheets/chunks)
            query_filter = QdrantModels.Filter(
                should=[
                    QdrantModels.FieldCondition(
                        key="source",
                        match=QdrantModels.MatchValue(
                            value=source,
                        ),
                    )
                    for source in sources
                ]
            )

        res = client.search(
            collection_name=collate_ix_name(name, QDRANT_IX_VER),
            query_vector=embeddings,
            query_filter=query_filter,
            limit=limit,
        )

        es = Elasticsearch(ELASTICSEARCH_URL, basic_auth=ELASTICSEARCH_CREDS)
        # FIXME: qdrant doesn't accept the hash id as string
        if name == "chunks":
            _uid = lambda x: bytes.fromhex(x.replace("-", "")).decode("utf8")
        else:
            _uid = lambda x: x
        hits = [
            _extract(
                es.get(index=collate_ix_name(name, ELASTICSEARCH_IX_VER), id=_uid(x.id))["_source"]
            )
            for x in res
            if x
        ]
        if do_unique_sheets:
            keep_idx = []
            seen_sheets = []
            for i, d in enumerate(hits):
                if d["url"] in seen_sheets:
                    continue
                keep_idx.append(i)
                seen_sheets.append(d["url"])

            hits = [hits[i] for i in keep_idx][: limit // 5]

    return hits


if __name__ == "__main__":
    hits = search("chunks", "test", 3, "bm25", None, None)

    pprint(hits)