import csv
import numpy as np

from elasticsearch_dsl import Index, Mapping, connections
from elasticsearch import helpers

from src import config

from src.utils.palm import create_embeddings


INDEX_NAME = 'knowledge-base'

es = connections.create_connection(
    hosts=config.ES_HOST,
    http_auth=(config.ES_USER, config.ES_PASS),
    ca_certs='http_ca.crt',
    timeout=120
)


def create_index(reset=False):
    """An index is like a 'database' in a relational database. It has a mapping which defines
    multiple types. Each document is a collection of fields, which each have their own data type.
    Mapping is the process of defining how a document, and the fields it contains, are stored
    and indexed.
    """

    if (Index(INDEX_NAME).exists() is True
            and reset is True):
        res = Index(INDEX_NAME).delete()
        print('Deleted the index...', res)

    m = Mapping()
    m.field('embedding_vector', 'dense_vector',
            dims=768, index=True, similarity='cosine')
    m.field('text', 'text')

    res = m.save(INDEX_NAME)
    print('Created the index...', res)


def generate_documents(input_file):
    """An iterator that selects the next passage and returns it as a document.
    In other words, this function helps index passages into individual documents.

    Yields:
        dict: document to be stored in elasticsearch.
    """
    with open(input_file, 'r', encoding='utf-8') as fi:
        # reader = csv.DictReader(fi, delimiter='\t')
        reader = csv.reader(fi, delimiter='\t')

        for idx, row in enumerate(reader):
            doc = {
                '_index': INDEX_NAME,
                '_id': int(idx),
                '_source': {
                    'embedding_vector': create_embeddings([row])[0],
                    'text': row,
                },
            }
            yield doc


def index_documents(input_file):
    """Indexes the entire large dataset without the need of loading them into memory.
    Consumes an iterator of actions, the creation of documents in our case,
    and sends them to elasticsearch in chunks.
    """
    n_success, n_failed = helpers.bulk(
        es, generate_documents(input_file))
    print('Indexed documents...', n_success, 'indexed,',
          'no errors.' if not n_failed else n_failed)


def search_knn(query_vector, k=5, method='approximate'):
    """Finds best passage by applying kNN.
    A k-nearest neighbor (kNN) search finds the k nearest vectors to a query vector,
    as measured by a similarity metric, cosine similarity in this case.

    Args:
        k (int, optional): Number of nearest vectors to search. Defaults to 5.
        method (str, optional): Search method to apply. \
            `approximate` kNN offers lower latency at the cost of slower indexing and imperfect accuracy (applicable in most cases).\
            `exact`, brute-force kNN guarantees accurate results but doesn’t scale well with large datasets. With this approach, a script_score query must scan each matching document to compute the vector function, which can result in slow search speeds. However, you can improve latency by using a query to limit the number of matching documents passed to the function. If you filter your data to a small subset of documents, you can get good search performance using this approach. Defaults to 'approximate'. See https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html for more information.

    Returns:
        list[dict[str, any]]: the document id, text, and cosine similarity of the k nearest vectors.
    """
    if method == 'approximate':
        res = es.search(
            index=INDEX_NAME,
            body={
                "size": k,
                "knn": {
                    'field': 'embedding_vector',
                    'k': k,
                    'num_candidates': 10,
                    'query_vector': query_vector
                },
                "_source": ['_id', 'embedding_vector', 'text'],
            })
    elif method == 'exact':
        res = es.search(  # pylint: disable=unexpected-keyword-arg
            index=INDEX_NAME,
            query={
                "script_score": {
                    "query": {
                        "match_all": {}
                    },
                    "script": {
                        "source": "cosineSimilarity(params.queryVector, 'embedding_vector') + 1.0",
                        "params": {
                            "queryVector": query_vector
                        }
                    }
                }
            })

    for hit in res['hits']['hits']:
        hit['_source']['embedding_vector'] = None
    print('Passage(s) found:', res)

    return [{'ref': hit['_id'],
             'text': hit['_source']['text'][0],
             'score': hit['_score'],
             } for hit in res['hits']['hits']]
