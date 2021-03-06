import argparse
import textwrap
import datetime
import re
import logging
from csv import DictReader
from distutils.util import strtobool
from time import time
from model import Base, ToDo
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker


logging.basicConfig(format='%(asctime)s %(levelname)s %(funcName)s[%(lineno)d] - %(message)s', level=logging.DEBUG)  # nopep8


FILL_STRING = '...'
MAX_TOPIC_LEN = 20
MAX_DESCRIPTION_LEN = 70

# date: dd.mm.yyyyy
REGEX_DATE = r'(\d{2}\.\d{2}\.\d{4})'
# single date
REGEX_DATE_SINGLE = '^' + REGEX_DATE + '$'
# date range: dd.mm.yyyy-dd.mm.yyyy
REGEX_DATE_RANGE = '^' + REGEX_DATE + '\-' + REGEX_DATE + '$'

# validating all list options
REGEX_VALIDATE_LIST_OPTION = r'\ball\b|\bopen\b|\bdone\b' +\
                             '|' + REGEX_DATE_SINGLE +\
                             '|' + REGEX_DATE_RANGE


def fill_with_test_data(session):
    '''
    Fill the DB with test data. The means:
    1. delete all data
    2. fill DB with test data
    '''
    # delete all todos
    session.query(ToDo).delete()
    session.commit()

    start = time()
    # read all test data and add them to the DB
    with open('fakedata.csv', 'r', encoding='utf-8-sig') as csv_file:
        reader = DictReader(csv_file)
        for row in reader:
            todo = ToDo(topic=row['Topic'],
                        done=strtobool(row['Done']),
                        due_date=datetime.datetime.strptime(row['DueDate'], '%d.%m.%Y'),
                        description=row['Description'],)
            if session.query(ToDo).filter(ToDo.topic == todo.topic).count() > 0:
                print('Topic already exists: ' + todo.topic + ' ' + todo.due_date.strftime('%d.%m.%Y'))
            session.add(todo)
    print('Runtime: ', time() - start)
    session.commit()


def print_todos(todos):
    '''
    print todos on o the console
    '''
    for todo in todos:
        if len(todo.topic) > MAX_TOPIC_LEN:
            topic = todo.topic[0:MAX_TOPIC_LEN - len(FILL_STRING)] + FILL_STRING
        else:
            topic = todo.topic
        if len(todo.description) > MAX_DESCRIPTION_LEN:
            description = todo.description[0:MAX_DESCRIPTION_LEN - len(FILL_STRING)] + FILL_STRING
        else:
            description = todo.description
        print('id:{0:04d} "{1:<{width1}s}" {2:>12s} {3:>7} {4:>{width2}}'.
              format(todo.id,
                     topic,
                     todo.due_date.strftime('%d.%m.%Y'),
                     str(todo.done),
                     description,
                     width1=MAX_TOPIC_LEN,
                     width2=MAX_DESCRIPTION_LEN + 2))


def add_todo(session):
    logging.debug('add todo')


def delete_todo(session):
    logging.debug('delete todo')


def get_todos(session, list_option='all'):
    ''' This function list todos depending on <list_option>
    parameter:
        session: DB session
        list_option: list option. Possible values are:
                        all:  ist all todos - incl. those are done
                        done: list all done todos
                        open: list all open todos
                        {dd.mm.yyyy}  list all open ToDos for the specified date
                        {dd.mm.yyyy}-{dd.mm.yyyy}  list all open ToDos for the specified periode
    exceptions:
        RuntimeError: thrown if list_option is unknown
    '''
    logging.debug('list todos')
    if list_option == 'all':
        # TODO: sort acording to ToDo.done
        todos = session.query(ToDo)
        return(todos)

    # list all done todos
    elif list_option == 'done':
        todos = session.query(ToDo).filter(ToDo.done)
        return(todos)

    # list all open todos
    elif list_option == 'open':
        todos = session.query(ToDo).filter(ToDo.done == False)      # nopep8 E712
        return(todos)

    # list all todos with a specific due date
    elif re.search(REGEX_DATE_SINGLE, list_option):
        date1 = re.search(REGEX_DATE_SINGLE, list_option)  # get date
        dt1 = datetime.datetime.strptime(date1.group(0), '%d.%m.%Y')
        todos = session.query(ToDo).filter(ToDo.due_date == dt1)
        return(todos)

    # list all todos within a specific date range
    elif re.search(REGEX_DATE_RANGE, list_option):
        date1 = re.search(REGEX_DATE_RANGE, list_option).group(1)    # get first date
        date2 = re.search(REGEX_DATE_RANGE, list_option).group(2)    # get second date
        dt1 = datetime.datetime.strptime(date1, '%d.%m.%Y')
        dt2 = datetime.datetime.strptime(date2, '%d.%m.%Y')
        logging.debug(dt1 <= dt2)
        todos = session.query(ToDo).filter(and_(ToDo.due_date >= dt1, ToDo.due_date <= dt2))
        return(todos)

    # unknown list option
    else:
        raise RuntimeError('unknown list option: ', list_option)


def create_session():
    """
    Creates a sesson object
    @return: session object
    """
    # Create an engine that stores data
    engine = create_engine('sqlite:///todo.sqlite')

    # Create all tables in the engine
    Base.metadata.create_all(engine)

    # Bind the engine to the metadata of the Base class so that the
    # declaratives can be accessed through a DBSession instance
    Base.metadata.bind = engine

    # A DBSession() instance establishes all conversations with the database
    # and represents a "staging zone" for all the objects loaded into the
    # database session object. Any change made against the objects in the
    # session won't be persisted into the database until you call
    # session.commit(). If you're not happy about the changes, you can
    # revert all of them back to the last commit by calling
    # session.rollback()
    DBSession = sessionmaker(bind=engine)
    return(DBSession())


def main():
    parser = argparse.ArgumentParser(description='Program for administrating a ToDo list.',
                                     usage='use "python %(prog)s --help" for more information',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-a', '--add',
                        action='store_true',
                        dest='add',
                        default=False,
                        required=False,
                        help='add a new ToDo topic')

    parser.add_argument('-d', '--delete',
                        action='store_true',
                        default=False,
                        required=False,
                        help='list ToDo topics')

    parser.add_argument('-l', '--list',
                        action='store',
                        dest='list_option',
                        nargs='?',
                        default=None,
                        required=False,
                        help=textwrap.dedent('''
                            list ToDos
                            all   list all ToDos including those which are done
                            open  list all open ToDos
                            done  list all done ToDos
                            {dd.mm.yyyy}  list all open ToDos for the specified date
                            {dd.mm.yyyy}-{dd.mm.yyyy}  list all open ToDos for the specified periode
                        ''')
                        )
    results = parser.parse_args()

    session = create_session()

    fill_with_test_data(session)

    if results.list_option:
        todos = get_todos(session, results.list_option)
        if todos:
            print_todos(todos)

    elif results.add:
        todos = add_todo(session)

    elif results.delete:
        todos = delete_todo(session)


if __name__ == "__main__":
    main()
