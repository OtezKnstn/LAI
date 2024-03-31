import os
# from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters
from oauth2client.service_account import ServiceAccountCredentials
from const import *

from google_calendar import CalendarClient
import gspread
import llm_train.rag as rag


GRADE = range(1)
CONFIRM = range(1)
class Client():
    def __init__(self) -> None:
        # self.app = ApplicationBuilder().token(token).build()
        #если проблемы с инетом
        self.app = ApplicationBuilder().token(BOT_TOKEN).read_timeout(100).write_timeout(100).build()

        conv_grade = ConversationHandler(
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
        #######################################
        conv_main = ConversationHandler(
        entry_points=[MessageHandler(filters= None, callback= self.textMessage),
                      CommandHandler("test", self.test)],
        states={
            CONFIRM:[
                MessageHandler(
                    filters.TEXT, self.setDate
                ),
                # MessageHandler(filters.Regex("^Something else...$"), self.confirmDate),
            ],
            
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), self.done)],
        )

        handlers = [CommandHandler("hello", self.hello),
                    conv_grade,
                    conv_main,
                    CommandHandler("start", self.startCommand),
                    CommandHandler("clear", self.clear),
                    # MessageHandler(filters= None, callback= self.textMessage)
                    ]
        self.app.add_handlers(handlers)
        self.wks = None
        #для гугл таблиц
        try:
            gscope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            gcredentials = 'test.json'
            credentials = ServiceAccountCredentials.from_json_keyfile_name(gcredentials, gscope)
            
            gdocument = 'llm'
            gc = gspread.authorize(credentials)
            self.wks = gc.open(gdocument).sheet1
        except:
            self.wks = None
            print("Не удалось подключиться к таблице")
        print("бот запущен")

    def run(self):
        self.app.run_polling()
    async def test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        context.user_data['date'] = "2024, 4, 2, 10, 0, 0"
    
    async def setDate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message.text == "Верно" or update.message.text == "верно":
            try:
                c = CalendarClient()
                response = c.create_google_calendar_event(update.effective_user.name, context.user_data['date'])
                await update.message.reply_text(response)
            except:
                await update.message.reply_text("Возникли проблемы с календарём, попробуйте позже")
        elif update.message.text == "Не верно" or update.message.text == "не верно":
            await update.message.reply_text("На какое число вы тогда хотите записаться?")
        else:
            keyboard = [
                [
                    InlineKeyboardButton("Верно", callback_data="Верно"),
                    InlineKeyboardButton("Не верно", callback_data="Не верно"),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Верно или не верно?", reply_markup=reply_markup)
            return CONFIRM
        context.user_data.pop('date')
        return ConversationHandler.END
    
    async def add_to_gsheet(self, message, response, user):
        self.wks.append_row([user, message, response, '-'])

    async def grade_to_answer(self, user, grade):
        buf_list = self.wks.findall(user)
        self.wks.update_cell(buf_list[-1].row, 4, grade)

    async def startCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text('Привет! Я бот. Как дела?')

    async def hello(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:        
        await update.message.reply_text(f'Hello {update.effective_user.first_name}')
    
    async def gradeCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        response = rag.answer_user_question_lm(update.message.text)
        # match = re.match(r"[0-9]{1,2}\, [0-9]{1,2}\, [0-9]{1,2}\, [0-9]{1, 2}\, [0-9]{1, 2}", response)
        if response[0] == "2" and len(response) < 25:
            keyboard = [
                [
                    InlineKeyboardButton("Верно", callback_data="Верно"),
                    InlineKeyboardButton("Не верно", callback_data="Не верно"),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            context.user_data['date'] = response
            y, m, d, h, min, sec = map(int, context.user_data['date'].split(', '))
            await update.message.reply_text(f"Проверьте правильноть записи:\n{d}.{m}.{y} в {h}:{min}?", reply_markup=reply_markup)
            return CONFIRM
        if self.wks is not None:
            await self.add_to_gsheet(update.message.text, response, update.effective_user.name)
        await update.message.reply_text(response)
        return ConversationHandler.END



if __name__ == '__main__':

    bot = Client()
    bot.run()
