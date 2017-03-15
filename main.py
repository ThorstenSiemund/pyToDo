import argparse
import textwrap
import datetime
import re
from csv import DictReader
from distutils.util import strtobool
from time import time
from model import Base, ToDo
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker


REGEX_LIST_OPTION = r'\b(\d{1,2})([dw])\b'  # one or two digit followed by a char ([d,w])
print(REGEX_LIST_OPTION)

# REGEX_DATE = r'\d{2}\.\d{2}\.\d{4}'         # date: dd.mm.yyyyy


# REGEX_DATE_RANGE = REGEX_DATE + '\-' + REGEX_DATE

# rslt = re.match(REGEX_DATE_RANGE, '12.23.2345-12.23.4683')
# print(rslt)


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
                print('Topic alreadyexists: ' + todo.topic + ' ' + todo.due_date.strftime('%d.%m.%Y'))
            session.add(todo)
    print('Runtime: ', time() - start)
    session.commit()


def list_todos(session, list_option='all'):
    ''' This function list todos depending on <list_option>
    parameter:
        session: DB session
        list_option: list option. Possible values are:
                        all:  ist all todos - incl. those are done
                        done: list all done todos
                        open: list all open todos
                        {x}d: list all open todos for the next {x} days
                        {x}w: list all open todos for the next {x,} weeks
    exceptions:
        RuntimeError: thrown if list_option is unknown
    '''
    # TODO: list all todos for a date e.g. 17.03.2017
    # TODO: list all todos for a special date range: 17.03.2017-23.03.2017
    # list all todos - incl. thse are done
    if list_option == 'all':
        for todo in session.query(ToDo):
            print(todo)

    # list all done todos
    elif list_option == 'done':
        for todo in session.query(ToDo).filter(ToDo.done):
            print(todo)

    # list all open todos
    elif list_option == 'open':
        for todo in session.query(ToDo).filter(ToDo.done == False):     # nopep8 E712
            print(todo)

    # list all todos during the interval {x} days or {x}weeks
    elif re.search(REGEX_LIST_OPTION, list_option):
        regex = re.search(REGEX_LIST_OPTION, list_option)
        # day interval?
        if regex.group(2) == 'd':
            td = (datetime.datetime.now() +
                  datetime.timedelta(days=int(regex.group(1))))
        # week interval?
        elif regex.group(2) == 'w':
            td = (datetime.datetime.now() +
                  datetime.timedelta(week=int(regex.group(1))))
        # unknown list option
        else:
            raise RuntimeError('unknown list option: ', list_option)
        # list all active todos in the given interval
        for todo in session.query(ToDo).filter(and_(ToDo.due_date <= td, ToDo.done == False)):   # nopep8 E712
            print(todo)
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


def ListOptionString(v):
    try:
        return re.match(r'\ball\b|\bopen\b|\bdone\b|(\d{1,2})([dw])', v).group(0)
    except:
        raise argparse.ArgumentTypeError("String '%s' does not match required format" % (v,))


def main():
    parser = argparse.ArgumentParser(description='Program for administrate a list fo ToDo.',
                                     usage='use "python %(prog)s --help" for more information',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-a', '-add',
                        action="store_true",
                        dest='add',
                        default=False,
                        required=False,
                        help='add a new ToDo topic')

    parser.add_argument('-d', '--delete',
                        action='store_true',
                        dest='delete_option',
                        required=False,
                        help='list ToDo topics')

    parser.add_argument('-l', '--list',
                        action='store',
                        type=ListOptionString,
                        # choices=['all', 'open', 'done', '{x}d', '{x}w'],
                        dest='list_option',
                        default=None,
                        required=False,
                        help=textwrap.dedent('''\
                            list ToDos
                            all   list all ToDos including those which are done
                            open  list all open ToDos
                            done  list all done ToDos
                            {x}d  list all open ToDos for he next {x} days (where {x} is 0..99)
                            {x}w  list all open ToDos for he next {x} weeks (where {x} is 0..99)
                        ''')
                        )
    # TODO: 'main.py -add' is throwing an exception
    # parser.add_argument('-ids', nargs='*', dest='ids', help='some ids')
    # print(parser.parse_args(['-h']))
    results = parser.parse_args()

    # print('-a: ', results.add)
    # print('-l: ', results.list_option)
    # print('-ids', results.ids)

    session = create_session()

    fill_with_test_data(session)

    if results.list_option:
        list_todos(session, results.list_option)

    pass


if __name__ == "__main__":
    main()
