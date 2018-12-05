import datetime


def date_format(data):

    for elem in data:
        date_str = elem['created_at']
        date_obj = datetime.datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
        elem['datetime'] = datetime.datetime.combine(date_obj.date(), date_obj.time())
