import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Boolean, String, DateTime


Base = declarative_base()


class ToDo(Base):
    __tablename__ = 'todo'
    id = Column(Integer, primary_key=True)
    topic = Column(String(255), nullable=False)
    done = Column(Boolean, default=False)
    due_date = Column(DateTime, default=datetime.datetime.now())
    description = Column(String(255))

    def __repr__(self):
        # TODO: cut Topic in he same way like description
        desc = ''
        MAX_STRING_LEN = 20
        due_date = self.due_date.strftime('%Y-%m-%d')
        if len(self.description) <= MAX_STRING_LEN:
            desc = self.description
        else:
            desc = self.description[0:MAX_STRING_LEN - 4] + '...'
        return('<ToDo (Topic: "%s", DueDate: "%s", Done="%s", Description: "%s")>' % (self.topic, due_date, self.done, desc))
