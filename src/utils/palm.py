# pylint: disable=missing-function-docstring, missing-module-docstring, line-too-long

import textwrap

from typing import List
from google.cloud import aiplatform
from vertexai.preview.language_models import TextGenerationModel, TextEmbeddingModel, ChatModel


from src import config

aiplatform.init(project=config.GCP_PROJECT)

embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
text_model = TextGenerationModel.from_pretrained("text-bison@001")
chat_model = ChatModel.from_pretrained("chat-bison@001")
chat = chat_model.start_chat(
    context='You are a helpful and informative bot that answers questions. Be sure to respond in a complete sentence, being comprehensive, including all relevant background information.')


def create_embeddings(passages: List[str]):
    embeddings = embedding_model.get_embeddings(passages)
    return [e.values for e in embeddings]


def generate_answer(prompt, mode):
    if mode == 'text':
        response = text_model.predict(
            prompt=prompt, temperature=0.8)
    elif mode == 'chat':
        response = chat.send_message(prompt, temperature=0.8)
    return response.text


def make_prompt(query, relevant_passage):
    escaped = relevant_passage.replace(
        "'", "").replace('"', "").replace("\n", " ")
    prompt = textwrap.dedent("""You are a helpful and informative bot that answers questions using text from the reference passage included below. \
  Be sure to respond in a complete sentence, being comprehensive, including all relevant background information. \
  However, you are talking to a non-technical audience, so be sure to break down complicated concepts and \
  strike a friendly and converstional tone. \
  If the passage is irrelevant to the answer, you may ignore it.
  QUESTION: '{query}'
  PASSAGE: '{relevant_passage}'

  ANSWER:
  """).format(query=query, relevant_passage=escaped)

    return prompt
