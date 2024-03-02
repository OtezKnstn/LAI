import pickle
import requests

from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from langchain.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)

import re




def create_embedding(text_data: str) -> None:
    """
    Функция create_embedding принимает текстовые данные в виде строки и создает эмбеддинги для каждого куска текста.
    Она разбивает входные данные на куски, создает для каждого куска объект Document,
    использует модель эмбеддингов для преобразования текста в векторы, а затем сохраняет эти векторы в объект Chroma и сохраняет объект в файл 'chroma.pkl' для дальнейшего использования..
    Функция также сохраняет объект Chroma в файл 'chroma.pkl' для дальнейшего использования.
    """
    source_documents = []
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1024, chunk_overlap=0)

    for chunk in text_splitter.split_text(text_data):
        source_documents.append(Document(page_content=chunk, metadata={}))

    embedding_model = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    chroma_db = Chroma.from_documents(source_documents, embedding_model)

    with open('chroma.pkl', 'wb') as file:
        pickle.dump(chroma_db, file)


def read_source_documents(google_docs_url: str) -> None:
    """
    Читает текстовые документы из Google Docs по заданному URL.
    """
    
    match_ = re.search('/document/d/([a-zA-Z0-9-_]+)', google_docs_url)
    if match_ is None:
        raise ValueError('Недопустимый URL Google Docs')
    doc_id = match_.group(1)

    response = requests.get(f'https://docs.google.com/document/d/{doc_id}/export?format=txt')
    response.raise_for_status()
    text = response.text
    create_embedding(text)
