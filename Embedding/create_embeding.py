import pickle

from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from langchain.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)


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

