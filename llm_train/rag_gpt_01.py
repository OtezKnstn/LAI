import re        # для работы с регулярными выражениями
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from openai import OpenAI
import os
from const import *
import codecs


API_KEY = OPEN_AI_API
LL_MODEL = "gpt-3.5-turbo"

client = OpenAI(
            # This is the default and can be omitted
            api_key=OPEN_AI_API,
        )

# Функция загруки содержимого текстового файла
def load_text(file_path):
    # Открытие файла для чтения
    with codecs.open(file_path, "r", encoding="utf-8", errors="ignore") as input_file:
        # Чтение содержимого файла
        content = input_file.read()
    return content


# Функция создания индексной базы знаний
def create_index_db(database: list):
    # Инициализирум модель эмбеддингов
    embeddings = OpenAIEmbeddings(openai_api_key=OPEN_AI_API)
    splitter = CharacterTextSplitter(separator="\n", chunk_size=512, chunk_overlap=0)
    for index, pdf in enumerate(database):
        content = PyPDFLoader(pdf)
        if index == 0:
            faiss_index = FAISS.from_documents(content.load_and_split(splitter), embeddings)
        else:
            faiss_index_i = FAISS.from_documents(content.load_and_split(splitter), embeddings)
            faiss_index.merge_from(faiss_index_i)

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
        {"role": "user", "content": f"Вот документ с информацией для ответа клиенту: {message_content}\n\n Вот вопрос клиента: \n{topic}"}
    ]

    completion = client.chat.completions.create(
            model=LL_MODEL,
            messages=messages,
            temperature=temp,
            stream=False,
        )
    # completion = openai.ChatCompletion.create(
    #     model=LL_MODEL,
    #     messages=messages,
    #     temperature=temp
    # )
    answer = completion.choices[0].message.content

    return answer  # возвращает ответ

# Загружаем текст Базы Знаний из файла
directory = "./data_base" #test
# directory = os.getcwd() + "/data_base"
data = os.listdir(directory)
database = []

for i in range(len(data)):
    if data[i].endswith('.pdf'):
        database.append(directory +"/" + data[i])
    

# Создаем индексную Базу Знаний
index_db = create_index_db(database)
# Загружаем промпт для модели, который будет подаваться в system
system = load_text('./llm_train/prompt.txt')



def answer_user_question(topic):
    # Ищем реливантные вопросу чанки и формируем контент для модели, который будет подаваться в user
    message_content = get_message_content(topic, index_db, k_num=2)
    # Делаем запрос в модель и получаем ответ модели
    answer = answer_index(system, topic, message_content, temp=0.2)
    return answer

if __name__ == '__main__':
    topic ="запиши меня на 2 апреля этого года на 10 утра"
    # print(database)
    answer, message_content = answer_user_question(topic)
    print(f'answer={answer}')
    topic ="расскажи про тарифы"
    answer, message_content = answer_user_question(topic)
    print(f'answer={answer}')

