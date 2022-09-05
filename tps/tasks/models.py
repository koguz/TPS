from django.db import models
from django.db.models.deletion import CASCADE, SET_NULL
from django.db.models.fields.related import ForeignKey
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User 
from django.utils.translation import gettext_lazy as _

def past_date_validator(value):
    import datetime 
    if datetime.date.today() >= value:
        raise ValidationError(
            _('%(value)s is in the past!'),
            params={'value': value},
        )

class Lecturer(models.Model):
    user = models.OneToOneField(User, on_delete=CASCADE) 

    def __str__(self):
        return self.getName()
    
    def getName(self):
        return self.user.first_name + " " + self.user.last_name

class MasterCourse(models.Model):
    code = models.CharField("Course Code", max_length=8)
    name = models.CharField("Course Name", max_length=256)

    def __str__(self):
        return self.code + " - " + self.name 
 
class Course(models.Model):
    masterCourse = models.ForeignKey(MasterCourse, on_delete=CASCADE)
    lecturer = models.ForeignKey(Lecturer, on_delete=SET_NULL, null=True)
    semester = models.CharField(max_length=128)
    group_weight = models.PositiveSmallIntegerField("Group Weight", default=40)
    individual_weight = models.PositiveSmallIntegerField("Individual Weight", default=60)
    active = models.BooleanField("Active", default=True)
    # TODO check if group + individual is 100 

    def __str__(self):
        return str(self.masterCourse) + " @ " + self.semester

    def get_current_milestone(self):
        import datetime 
        return self.milestone_set.all().order_by('due').exclude(due__lte=datetime.date.today())[0]

class Milestone(models.Model):
    course = models.ForeignKey(Course, on_delete=CASCADE)
    name = models.CharField("Milestone", max_length=128)
    description = models.TextField("Milestone Details")
    weight = models.PositiveSmallIntegerField("Weight", default=30)
    due = models.DateField("Due Date")

    def __str__(self):
        return self.name

class Team(models.Model):
    course = models.ForeignKey(Course, on_delete=CASCADE)
    name = models.CharField(max_length=256)
    github = models.CharField("Git Page", max_length=512, null=True)
    supervisor = models.ForeignKey(Lecturer, on_delete=SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.name 

    def get_all_milestone_points(self, m):
        p = 0
        for task in self.mastertask_set.all().filter(milestone=m):
            p = p + task.get_points() 
        return p 
    
    def get_all_accepted_points(self, m):
        p = 0
        for task in self.mastertask_set.all().filter(milestone=m):
            if task.status == 5:
                p = p + task.get_points() 
        return p 
    
    def get_milestone_list(self):
        milestone_list = {}
        for m in self.course.milestone_set.all():
            milestone_list[m.name] = self.get_team_points(m)
        return milestone_list 

    def get_team_points(self, m):
        g = 0
        if self.get_all_milestone_points(m) > 0:
            g = round((self.get_all_accepted_points(m) / self.get_all_milestone_points(m)) * 100)
        return g 

    def get_developer_average(self, m):
        return self.get_all_milestone_points(m) / len(self.developer_set.all())


class Developer(models.Model):
    user = models.OneToOneField(User, on_delete=CASCADE)
    team = models.ManyToManyField(Team, blank=True)

    # team = models.ForeignKey(Team, on_delete=SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.getName()
    
    def getName(self):
        return self.user.first_name + " " + self.user.last_name

    def get_all_accepted_points(self, m):
        p = 0
        for task in self.mastertask_set.all().filter(milestone=m):
            if task.status == 5:
                p = p + task.get_points() 
        return p 

    def get_developer_grade(self, m):
        t = self.team.all()[0]
        g = 0
        if t.get_developer_average(m) > 0:
            g = round((self.get_all_accepted_points(m) / t.get_developer_average(m)) * 100)
            if g > 100:
                g = 100
        return g 
    
    # we have to get the milestone names and points
    # for those milestones in a dictionary, so that i can loop through it in the template...
    def get_milestone_list(self):
        milestone_list = {}
        t = self.team.all()[0]
        for m in t.course.milestone_set.all():
            milestone_list[m.name] = self.get_developer_grade(m)
        return milestone_list

    def get_project_grade(self):
        team_grade = 0
        ind_grade = 0
        t = self.team.all()[0]
        c = t.course 
        for m in c.milestone_set.all():
            team_grade = team_grade + t.get_team_points(m) * (m.weight / 100)
            ind_grade  = ind_grade  + self.get_developer_grade(m) * (m.weight / 100)
        return round(team_grade * (c.group_weight / 100) + ind_grade * (c.individual_weight / 100))

    # TODO check permissions https://docs.djangoproject.com/en/3.2/topics/auth/default/

class MasterTask(models.Model):
    
    DIFFICULTY = (
        (1, 'Easy'),
        (2, 'Normal'),
        (3, 'Difficult')
    )

    STATUS = (
        (1, 'Proposed'),
        (2, 'Open'),
        (3, 'Completed'),
        (4, 'Rejected'),
        (5, 'Accepted')
    )

    milestone = models.ForeignKey(Milestone, on_delete=CASCADE)
    owner = models.ForeignKey(Developer, on_delete=CASCADE)
    team = models.ForeignKey(Team, on_delete=CASCADE)
    completed = models.DateField("Completion Date", null=True)
    difficulty = models.PositiveSmallIntegerField("Difficulty", choices=DIFFICULTY, default=2)
    status = models.PositiveSmallIntegerField("Status", choices=STATUS, default=1)

    def __str__(self):
        # this query gives me the last task title associated with this master task 
        return self.task_set.all().order_by('pk').reverse()[0].title
    
    # TODO 
    def getStatus(self):
        return self.STATUS[self.status-1][1]

    def getDifficulty(self):
        return self.DIFFICULTY[self.difficulty-1][1]

    def get_points(self):
        return self.difficulty * self.get_task().priority 
    
    def get_task(self):
        return self.task_set.all().order_by('pk').reverse()[0]

class Task(models.Model):
    PRIORITY = ( 
        (1, 'Low'),
        (2, 'Planned'),
        (3, 'Urgent')
    )
    masterTask = models.ForeignKey(MasterTask, on_delete=CASCADE)
    title = models.CharField("Brief Task Title", max_length=256)
    description = models.TextField("Description")
    promised_date = models.DateField("Promised Date", validators=[past_date_validator])
    priority = models.PositiveSmallIntegerField("Priority", choices=PRIORITY, default=2)
    version = models.IntegerField("version", default=1)

    def __str__(self):
        return self.title

    def getPriority(self):
        return self.PRIORITY[self.priority-1][1]

class Vote(models.Model):
    task = models.ForeignKey(Task, on_delete=CASCADE)
    owner = models.ForeignKey(Developer, on_delete=CASCADE)
    vote = models.BooleanField("Approve")
    status = models.SmallIntegerField("Status", default=1)

class Comment(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    mastertask = models.ForeignKey(MasterTask, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    body = models.TextField("Comment")
    file_url = models.URLField("URL", max_length=512, blank=True, null=True)
    approved = models.BooleanField("Approved", blank=True, null=True)
    date = models.DateTimeField("Date", auto_now_add=True)

    def __str__(self):
        return self.body

class Like(models.Model):
    owner = models.ForeignKey(Developer, on_delete=models.CASCADE)
    mastertask = models.ForeignKey(MasterTask, on_delete=models.CASCADE)
    liked = models.BooleanField("Liked")

class MasterTaskLog(models.Model):
    mastertask = models.ForeignKey(MasterTask, on_delete=models.CASCADE)
    taskstatus = models.CharField("Task Status", max_length=64)
    tarih = models.DateTimeField("Date", auto_now_add=True)
    log = models.TextField("Log")
    gizli = models.BooleanField("Gizli", default=False)

class TeamMilestoneGrade(models.Model):
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    grade = models.PositiveSmallIntegerField("Grade", default=0)


