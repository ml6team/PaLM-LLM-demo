# pylint: disable=missing-function-docstring
import argparse

from flask import Flask, render_template, request

from src.utils.elasticsearch import search_knn
from src.utils.palm import create_embeddings, generate_answer, make_prompt


# create a flask instance
app = Flask(__name__)


@app.route("/")
def index():
    return render_template('chat.html', rag=app.config['rag'])


@app.route("/get", methods=["GET", "POST"])
def chat():
    input = request.form["msg"]

    if app.config['rag'] is True:
        resp = get_rag_chat_response(input)
    else:
        resp = get_no_rag_chat_response(input)

    return resp


def get_rag_chat_response(query):
    # generate embedding of query
    prompt_embedding = create_embeddings([query])[0]

    # find best passage, k=1 so only one list entry
    passage_dict = search_knn(query_vector=prompt_embedding,
                              k=1,
                              method='approximate')[0]

    # engineer prompt to instruct API to cleverly use the passage
    prompt = make_prompt(query=query, relevant_passage=passage_dict['text'])

    # find the answer to the query
    response = generate_answer(prompt, mode='text')

    return {'response': response,
            'ref': 'document ' + str(passage_dict['ref']),
            'score': f'{passage_dict["score"]:.2f}'}


def get_no_rag_chat_response(query):
    # find the answer to the query
    response = generate_answer(query, mode='chat')

    return {'response': response}


if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-rag', help='Runs the chatbot without RAG functionality.',
                        action=argparse.BooleanOptionalAction)
    args = parser.parse_args()
    app.config['rag'] = True if args.no_rag is None else False

    # run flask application (chatbot)
    app.run(debug=True)
