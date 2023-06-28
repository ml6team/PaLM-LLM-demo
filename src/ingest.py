import argparse

from src.utils.elasticsearch import create_index, index_documents  # pylint: disable=import-error


if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', help='The input file (TSV) to be used for ingestion.',
                        type=str, default='data/documents_small.tsv')
    parser.add_argument('--reset-index', help='Resets the index (removes documents in elasticsearch)',
                        action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()

    # create index and populate
    create_index(reset=args.reset_index)
    index_documents(args.input_file)
