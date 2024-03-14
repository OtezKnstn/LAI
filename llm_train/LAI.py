from openai import OpenAI
import json
import requests

from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document

from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)

import re
import tiktoken



class LAI():
    def __init__(self):
        self.url = "http://serv.sae.ru:8888/v1"
        self.api = "not-needed"

    def createPromt(self, promt):
        return promt

    def sendRequest(self, system, promt):
        client = OpenAI(base_url=self.url, api_key=self.api)
        response = client.chat.completions.create(
            model="saiga_mistral_7b-AWQ",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": promt}
            ],
            temperature=0.9,
            max_tokens=1000
        )
        return response
    
    def getAnswer(self, response):
        response_dict = json.loads(response.json())
        answer = response_dict["choices"][0]["message"]["content"] #Переписать (Неправильный путь)
        return answer

    def answer(self, user_request):
        return self.getAnswer(self.sendRequest(self.createPromt(user_request)))
    
    def load_search_indexes(self, url: str) -> str:
        match_ = re.search('/document/d/([a-zA-Z0-9-_]+)', url)
        if match_ is None:
            raise ValueError('Invalid Google Docs URL')
        doc_id = match_.group(1)

        response = requests.get(f'https://docs.google.com/document/d/{doc_id}/export?format=txt')
        response.raise_for_status()
        text = response.text
        return self.create_embedding(text)
    
    def answer_index(self, system, topic, search_index, temp = 1, verbose = 0):       
        docs = search_index.similarity_search(topic, k=4)
        message_content = re.sub(r'\n{2}', ' ', '\n '.join([f'\nОтрывок документа №{i+1}\n=====================' + doc.page_content + '\n' for i, doc in enumerate(docs)]))
        print(self.sendRequest(system + f"{message_content}", topic))

    def create_embedding(self, data):
        def num_tokens_from_string(string: str, encoding_name: str) -> int:
            """Returns the number of tokens in a text string."""
            encoding = tiktoken.get_encoding(encoding_name)
            num_tokens = len(encoding.encode(string))
            return num_tokens

        source_chunks = []
        splitter = CharacterTextSplitter(separator="\n", chunk_size=1024, chunk_overlap=0)
        

        for chunk in splitter.split_text(data):
            source_chunks.append(Document(page_content=chunk, metadata={}))
        embedding_function = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        # Создание индексов документа
        db = Chroma.from_documents(source_chunks, embedding_function)
        print(type(db))
        #search_index = Chroma.from_documents(source_chunks, OpenAIEmbeddings(), )
        
        count_token = num_tokens_from_string(' '.join([x.page_content for x in source_chunks]), "cl100k_base")
        return db


    
lai = LAI()


text = "Здравствуйте, меня зовут Константин. Какой адрес у вашего магазина. Я живу в Южном регионе"

marketing_index = lai.load_search_indexes('https://docs.google.com/document/d/1gCvcpAgRrVjON801fBgwPBYyo46b3xT41bvxR_hN_b4/edit')

marketing_chat_promt = '''Ты менеджер поддержки в чате компании, компания продает товары разного назначения. 
У тебя есть большой документ со всеми материалами о продуктах компании. 
Тебе задает вопрос клиент в чате, дай ему ответ, опираясь на документ, постарайся ответить так, чтобы человек захотел после ответа купить товар. 
и отвечай максимально точно по документу, не придумывай ничего от себя. 
Документ с информацией для ответа клиенту: '''



lai.answer_index(
    marketing_chat_promt,
    text,
    marketing_index
)

#print(lai.answer(text))

"""from langchain.embeddings import SelfHostedHuggingFaceEmbeddings
import runhouse as rh
model_name = "sentence-transformers/all-mpnet-base-v2"
gpu = rh.cluster(name="rh-a10x", instance_type="A100:1")
hf = SelfHostedHuggingFaceEmbeddings(model_name=model_name, hardware=gpu)"""



# Выбор модели и токенизатора
"""model_name = "sentence-transformers/all-mpnet-base-v2"
model = AutoModel.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Подготовка текста
text = "Ваш текст здесь."

# Токенизация текста
tokens = tokenizer(text, return_tensors="pt")

# Получение векторного представления
outputs = model(**tokens)
vector = outputs.last_hidden_state.mean(dim=1).squeeze().detach().numpy()

print(vector)"""