"""
Файл с описанием класса подклюения к БД
"""
# pylint: disable = import-error, invalid-name, line-too-long
import psycopg2


class Saver:
    """
    Сохранения состояния пользователя
    """
    # pylint: disable = too-many-arguments
    def __init__(self, connstr=None, database='user_data', user='admin',
                 password='password', host='127.0.0.1', port=80, table='searched_users'):
        """
        Создает соединение с базой данных PostgreSQL.
        """

        if connstr is not None:
            try:
                self.connection = psycopg2.connect(connstr)
            except psycopg2.ProgrammingError as e:
                print(f"Ошибка при подключении к базе данных: {e}")
                self.connection = None
                return
        else:
            try:
                self.connection = psycopg2.connect(
                    database=database,
                    user=user,
                    password=password,
                    host=host,
                    port=port
                )
            except psycopg2.ProgrammingError as e:
                print(f"Ошибка при подключении к базе данных: {e}")
                self.connection = None
                return

        # Задаем название таблицы
        self.table = table
        self.check_table()
        print('Успешное подключение к базе данных!')

    def create_table(self):
        """
        Создание таблицы
        """
        with self.connection.cursor() as cursor:
            query = f"""CREATE TABLE IF NOT EXISTS {self.table} (
                user_id INTEGER PRIMARY KEY,
                searched_users INTEGER[] NOT NULL
            );
            """

            cursor.execute(query)
            self.connection.commit()

    def check_table(self):
        """
        Интерактивная проверка существования таблицы
        :return:
        """
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s);", (self.table,))
            result = cursor.fetchone()
            if result[0]:
                print('База существует, запускаю бота')
                return
            else:
                i = None
                # Просим вводи пользователя
                while i not in ['Y', 'N']:
                    # Вводим, пока не Y или N
                    i = input('Базы нет, создаем? Y/N ')
                # Выполняем действие
                if i == 'Y':
                    self.create_table()
                    print('Таблица создана, запускаю бота!')
                else:
                    print('Выхожу...')
                    exit()

    def save_session_to_db(self, user_id, searched_users):
        """
        Сохраняет или обновляет сессию пользователя в базе данных
        :param user_id:          Id пользователя ВКонтакте.
        :param searched_users:   Найденные пользователи
        """
        print(searched_users)
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {self.table} (user_id, searched_users)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    searched_users = {self.table}.searched_users || %s;
                """,
                (user_id, searched_users, searched_users)
            )
            self.connection.commit()

    def get_user_data_from_db(self, user_id):
        """
        Извлечение данных о пользователе из базы данных
        :param user_id: Id пользователя
        :return:        list при существовании данных, иначе None
        """
        with self.connection.cursor() as cursor:
            cursor.execute(f" SELECT searched_users FROM {self.table} WHERE user_id = %s;", (user_id,))
            result = cursor.fetchone()

        # Если есть данные
        return result[0] if result else []
