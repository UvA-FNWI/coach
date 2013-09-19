import re
import random
import string

from tincan_api import TinCan

# To ensure iktel login
IKTEL_URL_FORMAT = "http://www.iktel.nl/postlogin?continue=%s&login_hint=%s"

def fix_url(url, request):#{{{
    """Make sure the iktel lings go through the appengine login first."""
    if re.search('www.iktel.nl', url):
        return IKTEL_URL_FORMAT % (url, request.GET.get('email'));
    return url#}}}

def aggregate_statements(statements):#{{{
    table = {}
    for stmt in statements:
        if stmt['user'] in table:
            if stmt['activity'] in table[stmt['user']]:
                competitor = table[stmt['user']][stmt['activity']]
                if competitor['time'] < stmt['time']:
                    if competitor['verb'] == TinCan.VERBS['completed']['id']:
                        if stmt['verb'] == TinCan.VERBS['completed']['id']:
                            table[stmt['user']][stmt['activity']] = stmt
                    else:
                        table[stmt['user']][stmt['activity']] = stmt
            else:
                table[stmt['user']][stmt['activity']] = stmt
        else:
            table[stmt['user']] = {stmt['activity'] : stmt}
    aggregated_statements = []
    for user in table:
        for activity in table[user]:
            aggregated_statements.append(table[user][activity])
    return aggregated_statements#}}}

def split_statements(statements):#{{{
    """Split statements by type:
        assignments
        exercises
        video
        rest
    """
    result = {'assignments' : [], 'exercises' : [], 'video' : [], 'rest' : []}
    for statement in statements:
        try:
            type = statement['type']
        except KeyError:
            continue
        if type == TinCan.ACTIVITY_TYPES['assessment']:
            result['assignments'].append(statement)
        elif type == TinCan.ACTIVITY_TYPES['question']:
            result['exercises'].append(statement)
        elif type == TinCan.ACTIVITY_TYPES['media']:
            result['video'].append(statement)
        else:
            result['rest'].append(statement)
    return result#}}}

def f_score(confidence, support, beta=1):#{{{
    return (1 + beta ** 2) * ((confidence * support) /
                              (beta ** 2 * confidence + support))#}}}

def rand_id():#{{{
    """Generate a random ID for use in html DOM elements."""
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in range(10))#}}}
