import datetime
from pytz import timezone
from google.oauth2 import service_account
import googleapiclient.discovery

SERVICE_ACCOUNT_FILE = 'calendar-gpt-test-id.json'
CALENDAR_ID = 'ee29acc6700287d4d46387794b638d1616d8075d8198788220050d9eefb9288e@group.calendar.google.com'

class CalendarClient:
    def __init__(self):
        pass

    def find_next_available_time(self, service, start_time, duration_hours):
        current_time = start_time
        end_time = start_time + datetime.timedelta(hours=duration_hours)
        
        while self.check_event_conflict(service, current_time, end_time):
            current_time += datetime.timedelta(hours=1)
            end_time = current_time + datetime.timedelta(hours=duration_hours)
        
        return current_time

    def check_event_conflict(self, service, start_time, end_time):
        try:
            events_result = service.events().list(
                calendarId=CALENDAR_ID,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True
            ).execute()
            events = events_result.get('items', [])
            return len(events) > 0
        except Exception as e:
            print(f'Произошла ошибка при проверке событий: {e}')
            return True

    def create_google_calendar_event(self, client_name : str, date : str, duration_hours : int=1) -> str:
        # Авторизация с использованием файла с учетными данными
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/calendar'])

        # Создание клиента для работы с API Google Календарь
        service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
        
        y, m, d, h, min, sec =map(int,date.split(', '))
        start_time = datetime.datetime(y, m, d, h, min, sec, tzinfo=datetime.timezone.utc)
        
        moscow_timezone = timezone('Europe/Moscow')
        start_time = start_time.astimezone(moscow_timezone)
        end_time = start_time + datetime.timedelta(hours=duration_hours)

        if not self.check_event_conflict(service, start_time, end_time):
            event = {
                'summary': f'Запись: {client_name}',
                'description': f'Клиент: {client_name}',
                'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Europe/Moscow'},
                'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Europe/Moscow'},
                'reminders': {'useDefault': False},
            }

            # Отправка запроса для создания события
            event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
            return f'Событие успешно добавлено: {event.get("htmlLink")}'
        else:
            next_available_time = self.find_next_available_time(service, start_time, duration_hours)
            return f'На это время уже запланировано другое событие. Следующее доступное время: {next_available_time}'

if __name__ == '__main__':
    # Пример использования класса
    client_name = 'лалалэй'
    start_time = datetime.datetime(2024, 3, 24, 16, 0, 0, tzinfo=datetime.timezone.utc)  # Пример времени записи
    duration_hours = 1  # Продолжительность записи в часах

    calendar_client = CalendarClient()
    calendar_client.create_google_calendar_event(client_name, start_time, duration_hours)
