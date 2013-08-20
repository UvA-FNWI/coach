from random import randint
from random import gauss
from dashboard.models import Activity

def generate_assessment_users(u,a):
    """
    generate u users with a assessments
    """
    for i in range(u):
        user = "mailto:fakeuser%d@student.uva.nl" % (i,)
        generate_assessments(user,a)

def generate_assessments(user, n):
    """
    generate a assessment activities for user
    """
    activity = "http://www.example.com/fake/assessment/%d" % (randint(1,1000),)
    value = round(gauss(50,15))

    act = Activity(user=user,
                   type="http://adlnet.gov/expapi/activities/assessment",
                   verb="http://adlnet.gov/expapi/verbs/completed",
                   activity=activity,
                   value=value,
                   name="Fake",
                   description="Fake Assessment")
    act.save()
