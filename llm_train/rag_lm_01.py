import re        # для работы с регулярными выражениями
import codecs
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
# import openai
from openai import OpenAI
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
import os
from datetime import datetime

client = OpenAI(
                base_url="http://serv.sae.ru:8888/v1",
                # base_url="http://localhost:1234/v1",
                api_key= "no need"
            )

# Функция загруки содержимого текстового файла
def load_text(file_path):
    # Открытие файла для чтения
    with codecs.open(file_path, "r", encoding="utf-8", errors="ignore") as input_file:
        # Чтение содержимого файла
        content = input_file.read()
    return content

# Функция создания индексной базы знаний
def create_index_db(database):
    # model_id = 'sentence-transformers/all-MiniLM-L6-v2'
    model_id = 'intfloat/multilingual-e5-large'
    model_kwargs = {'device': 'cpu'}
    # model_kwargs = {'device': 'cuda'}
    embeddings = HuggingFaceEmbeddings(
      model_name=model_id,
      model_kwargs=model_kwargs
    )
    splitter = CharacterTextSplitter(separator="\n", chunk_size=512, chunk_overlap=0)
    for index, doc in enumerate(database):
        # content = PyPDFLoader(doc)
        content = Docx2txtLoader(doc)
        if index == 0:
            faiss_index = FAISS.from_documents(content.load_and_split(splitter), embeddings)
        else:
            faiss_index_i = FAISS.from_documents(content.load_and_split(splitter), embeddings)
            faiss_index.merge_from(faiss_index_i)
    # faiss_index.save_local()
    return faiss_index

# Функция получения релевантные чанков из индексной базы знаний на основе заданной темы
def get_message_content(topic, index_db, k_num):
    # Поиск релевантных отрезков из базы знаний
    docs = index_db.similarity_search(topic, k = k_num)
    message_content = re.sub(r'\n{2}', ' ', '\n '.join([f'\n#### Отрывок из документа №{i+1}####\n' + doc.page_content + '\n' for i, doc in enumerate(docs)]))
    print(f"message_content={message_content}")
    return message_content

# Функция отправки запроса в модель и получения ответа от модели
def answer_index(system, topic, message_content, temp):
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Вот документ для ответа клиенту: {message_content}\nСегодняшняя дата{datetime.today().strftime('%Y-%m-%d %H:%M:%S')}\n Вот вопрос клиента:{topic}"}
    ]
    completion = client.chat.completions.create(
        model='no need anymore',
        messages=messages,
        temperature=temp,
        stream=False
    )
    answer = completion.choices[0].message.content

    return answer  # возвращает ответ

# Загружаем текст Базы Знаний из файла
directory = "./data_base" #test
# directory = os.getcwd() + "/data_base"
data = os.listdir(directory)
database = []

for i in range(len(data)):
    if data[i].endswith('.docx'):
        database.append(directory +"/" + data[i])
    

# Создаем индексную Базу Знаний
index_db = create_index_db(database)
# Загружаем промпт для модели, который будет подаваться в system
system = load_text('./llm_train/prompt.txt')



def answer_user_question(topic):
    # Ищем реливантные вопросу чанки и формируем контент для модели, который будет подаваться в user
    message_content = get_message_content(topic, index_db, k_num=3)
    # Делаем запрос в модель и получаем ответ модели
    answer = answer_index(system, topic, message_content, temp=0.2)
    return answer

if __name__ == '__main__':
    while(1):
        topic = input('user: ')
        answer, message_content = answer_user_question(topic)
        print(f'answer={answer}')
        

