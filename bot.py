import os
# from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from llm_train.LAI import LAI

# load_dotenv()

TOKEN = ""
GRADE = 1
print(TOKEN)
class Client():
    def __init__(self) -> None:
        # self.app = ApplicationBuilder().token(token).build()
        #если проблемы с инетом
        self.app = ApplicationBuilder().token(TOKEN).read_timeout(100).write_timeout(100).build()

        self.lai = LAI()
        

        conv_handler = ConversationHandler(
        entry_points=[CommandHandler("grade", self.gradeCommand)],
        states={
            GRADE:[
                MessageHandler(
                    filters.Regex("^(1|2|3|4|5|6|7|8|9|10)$"), self.setGrade
                ),
                MessageHandler(filters.Regex("^Something else...$"), self.setGrade),
            ],
            
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), self.done)],
        )
        
        handlers = [CommandHandler("hello", self.hello),
                    conv_handler,
                    CommandHandler("start", self.startCommand),
                    CommandHandler("clear", self.clear),
                    MessageHandler(filters= None, callback= self.textMessage)
                    ]
        self.app.add_handlers(handlers)

        #для гугл таблиц
        gscope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        gcredentials = 'test.json'
        credentials = ServiceAccountCredentials.from_json_keyfile_name(gcredentials, gscope)
        
        gdocument = 'llm'
        gc = gspread.authorize(credentials)
        self.wks = gc.open(gdocument).sheet1
        print("бот запущен")

    def run(self):
        self.app.run_polling()

    async def add_to_gsheet(self, message, response, user):
        self.wks.append_row([user, message, response, '-'])

    async def grade_to_answer(self, user, grade):
        buf_list = self.wks.findall(user)
        self.wks.update_cell(buf_list[-1].row, 4, grade)

    async def startCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text('Привет, давай пообщаемся?')

    async def hello(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:        
        await update.message.reply_text(f'Hello {update.effective_user.first_name}')
    
    async def gradeCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # await self.grade_to_answer(update.effective_user.name)
        await update.message.reply_text(f'Поставьте оценку ответу от 0 до 10')
        return GRADE

    async def setGrade(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.grade_to_answer(update.effective_user.name, update.message.text)
        await update.message.reply_text(f'спасибо за вашу оценку')
        return ConversationHandler.END

    async def done(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(context.user_data)
        await update.message.reply_text(f'чем ещё я могу помочь?')
        return ConversationHandler.END
    
    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        context.chat_data.clear()
        await update.message.reply_text('чат очищен')

    async def textMessage(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message.text in context.chat_data:
            await self.add_to_gsheet(update.message.text, context.chat_data[update.message.text], update.effective_user.name)
            await update.message.reply_text(context.chat_data[update.message.text])
            return
        # response = f'Получил Ваше сообщение: {update.message.text}'
        while response == '':
            response, chunk = self.lai.answer_index(update.message.text)
            print("отправил запрос")
        print(chunk)
        await self.add_to_gsheet(update.message.text, response, update.effective_user.name)
        await update.message.reply_text(response)
        context.chat_data[update.message.text] = response
        print(context.chat_data,"\n")


if __name__ == '__main__':

    bot = Client()
    bot.run()
