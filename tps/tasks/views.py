from difflib import diff_bytes
from doctest import master
from re import T
from tokenize import group
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash 
from django.contrib.auth.models import Group, User
from django.contrib.auth.forms import PasswordChangeForm
from django.http.response import HttpResponse
# from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


from tasks.models import *
from .forms import CommentForm, CourseForm, MasterCourseForm, MilestoneForm, TaskForm, TeamFormStd


# Create your views here.

def saveLog(mt:MasterTask, message, gizli:bool = False):
    l = MasterTaskLog()
    l.mastertask = mt 
    l.taskstatus = mt.getStatus()
    l.log = message
    l.gizli = gizli 
    l.save() 

@login_required 
def index(request):
    from datetime import date 
    bugun = date.today()
    for mt in MasterTask.objects.all():
        task = mt.get_task()
        if mt.milestone.due < bugun and mt.status < 4:
            mt.status = 4
            mt.save()
            saveLog(mt, "Task is rejected because milestone is due.")
        if task.promised_date < bugun and mt.status < 4:
            mt.status = 4 
            mt.save()
            saveLog(mt, "Task is rejected because due date has passed.")
    
    # redirect to another page for lecturer! 
    try:
        d:Developer = Developer.objects.get(user=request.user)
        return redirect('team_view')
    except ObjectDoesNotExist:
        try: 
            l:Lecturer = Lecturer.objects.get(user=request.user)
            return redirect('lecturer_view')
        except ObjectDoesNotExist:
            return redirect('logout')

def update_view(request):
    return render(request, 'tasks/updates.html')

@login_required 
def team_view(request):
    d:Developer = Developer.objects.get(user=request.user)
    t:Team = d.team.all()[0]
    teams:Team([]) = d.team.all()
    devs = Developer.objects.all().filter(team=t)
    # TODO 
    milestone = t.course.get_current_milestone() # Milestone.objects.all().filter(course=t.course).order_by('due')[0]
    mt = MasterTask.objects.all().filter(team=t).order_by('pk').reverse()[:10]
    context = {
        'page_title': 'Team Home',
        'tasks': mt,
        'team': t,
        'devs': devs,
        'milestone': milestone,
        'teams': teams
    }
    return render(request, 'tasks/index.html', context)


@login_required
def edit_task(request, task_id):
    mt:MasterTask = get_object_or_404(MasterTask, pk=task_id)
    t:Task = Task.objects.all().filter(masterTask=mt).order_by('pk').reverse()[0]
    d:Developer = Developer.objects.get(user=request.user)
    tm = d.team.all()[0]
    if mt.owner != d: # return to team view if the owner of the task is not this user
        return redirect('team_view')
    if mt.status != 1: # return to team view if the master task is not 1 (proposed)
        return redirect('team_view')
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task:Task = form.save(commit=False) 
            task.pk = None 
            task.masterTask = mt 
            task.version = task.version + 1 
            task.save()

            devs = Developer.objects.all().filter(team=tm)

            receivers = []

            for developer in devs:
                if developer != d:
                    receivers.append(developer.user.email)

            subject = 'TPS:Notification || A task has been edited!'
            contentList = [
                'Edited by: ' + str(mt.owner), 
                'Title: ' + task.title,
                'Description: ' + task.description,
                'Priortiy: ' + task.getPriority(),
                'Due date: '+ str(task.promised_date)
            ]
            url = request._current_scheme_host + "/tasks/" + str(task.masterTask_id)

            html_message = render_to_string('tasks/email_template.html',
            {'title':'A task has been edited.', 'contentList': contentList, 'url':url, 'background_color': '#003399'})

            plain_message = strip_tags(html_message)
            from_email = 'no-reply@tps.info.tr'

            send_mail(subject, plain_message, from_email, receivers, html_message=html_message)
            saveLog(mt, "Task is edited by " + str(d) + ".")

            return redirect('view_task', task_id)
        else: 
            return redirect('team_view')
    else:
        form = TaskForm(instance=t)
        context = {
            'page_title': 'Edit task',
            'form': form, 
            'mastertask': mt
        }
        return render(request, "tasks/task_edit.html", context)

@login_required
def create_task(request):
    d = Developer.objects.get(user=request.user)
    t:Team = d.team.all()[0]
    teams: Team([]) = d.team.all()
    milestone = t.course.get_current_milestone() #Milestone.objects.all().filter(course=t.course).order_by('due')[0]
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            mastertask = MasterTask()            
            mastertask.milestone = milestone
            mastertask.owner = d
            mastertask.team = t
            mastertask.save() 
            task:Task = form.save(commit=False)
            task.masterTask = mastertask 
            task.save()
            mastertask.team.developer_set

            devs = Developer.objects.all().filter(team=t)

            receivers = []

            for developer in devs:
                if developer != d:
                    receivers.append(developer.user.email)

            contentList = [
                'Creator: ' + str(mastertask.owner),
                'Title: ' + task.title,
                'Description: ' + task.description,
                'Priority: ' + task.getPriority(),
                'Due date: ' + str(task.promised_date)
            ]

            subject = 'TPS:Notification || A task has been created'

            url = request._current_scheme_host + "/tasks/" + str(task.masterTask_id)

            html_message = render_to_string('tasks/email_template.html',
            {'title':'A task has been created!', 'contentList':contentList, 'url': url, 'background_color': '#003399'})

            plain_message = strip_tags(html_message)
            from_email = 'no-reply@tps.info.tr'

            send_mail(subject, plain_message, from_email, receivers, html_message=html_message)
            saveLog(mastertask, "Task is created by " + str(d) + ".")
            return redirect('team_view')
        else:
            context={'page_title': 'Create New Task', 'form': form, 'milestone': milestone}
            return render(request, "tasks/task_create.html", context)
            # return redirect('team_view')
    else:
        form = TaskForm()
        context = {
            'page_title': 'Create New Task',
            'form': form, 
            'milestone': milestone
        } 
        return render(request, "tasks/task_create.html", context)

@login_required 
def complete_task(request, task_id):
    mt:MasterTask = get_object_or_404(MasterTask, pk=task_id)
    t:Task = Task.objects.all().filter(masterTask=mt).order_by('pk').reverse()[0]
    d:Developer = Developer.objects.get(user=request.user)
    tm = d.team.all()[0]
    if mt.owner != d:
        return redirect('team_view')
    if request.method == 'POST':
        mt:MasterTask = get_object_or_404(MasterTask, pk=task_id)
        t:Task = Task.objects.all().filter(masterTask=mt).order_by('pk').reverse()[0]
        mt.status = 3 
        mt.difficulty = int(request.POST["difficulty"])
        mt.save()

        difficulty = str
        if mt.difficulty == 1:
            difficulty = 'Easy'
        elif mt.difficulty == 2:
            difficulty = 'Normal'
        elif mt.difficulty == 3:
            difficulty = 'Difficult'

        devs = Developer.objects.all().filter(team=tm)

        receivers = []

        for developer in devs:
            if developer != d:
                receivers.append(developer.user.email)
 
        subject = 'TPS:Notification || A task has been completed'

        contentList = [
            'Creator: ' + str(mt.owner), 
            'Title: ' + t.title,
            'Description: ' + t.description,
            'Priortiy: ' + t.getPriority(),
            'Difficulty: ' + difficulty,
            'Due date: '+ str(t.promised_date)
        ]

        url = request._current_scheme_host + "/tasks/" + str(t.masterTask_id)

        html_message = render_to_string('tasks/email_template.html',
        {'title':'A task has been completed!', 'contentList': contentList, 'url':url, 'background_color': '#003399'})

        plain_message = strip_tags(html_message)
        from_email = 'no-reply@tps.info.tr'

        send_mail(subject, plain_message, from_email, receivers, html_message=html_message)       
        saveLog(mt, "Task is completed by " + str(d) + ".")
        
        return redirect('view_task', task_id)
    else: 
        return redirect('team_view')

@login_required 
def edit_team(request):
    d:Developer = Developer.objects.get(user=request.user)
    t:Team = d.team.all()[0]
    print(t.name, t.github)
    if request.method == 'POST':
        form = TeamFormStd(request.POST)
        if form.is_valid():
            tnew = form.save(commit=False)
            tnew.pk = t.pk
            tnew.supervisor = t.supervisor 
            tnew.course = t.course
            tnew.save()
            return redirect('team_view')
    else:
        form = TeamFormStd(instance=t)
        context = {
            'page_title': 'Edit Team Information',
            'form': form
        }
        return render(request, "tasks/team_edit_std.html", context)


@login_required 
def like_task(request, task_id, liked):
    mt:MasterTask = get_object_or_404(MasterTask, pk=task_id)
    d:Developer = Developer.objects.get(user=request.user)
    if mt.owner == d:
        return redirect('team_view')
    try:
        # if like object exists, toggle like
        like = Like.objects.get(owner=d, mastertask=mt)
        if liked == 1 and like.liked:
            like.delete() 
            saveLog(mt, "Like removed by "+ str(d) + ".", True)
        elif liked == 0 and not like.liked:
            like.delete() 
            saveLog(mt, "Dislike removed by "+ str(d) + ".", True)
        elif liked == 1 and not like.liked:
            like.liked = True 
            like.save() 
            saveLog(mt, "Task liked by "+ str(d) + ".", True)
        elif liked == 0 and like.liked: 
            like.liked = False 
            like.save() 
            saveLog(mt, "Task disliked by "+ str(d) + ".", True)
    except ObjectDoesNotExist:
        like = Like()
        like.owner = d 
        like.mastertask = mt 
        if liked == 1:
            like.liked = True 
            saveLog(mt, "Task liked by "+ str(d) + ".", True)
        else:
            like.liked = False 
            saveLog(mt, "Task disliked by "+ str(d) + ".", True)
        like.save() 
    return redirect('view_task', task_id)



@login_required 
def view_task(request, task_id):
    mt:MasterTask = get_object_or_404(MasterTask, pk=task_id)
    t:Task = Task.objects.all().filter(masterTask=mt).order_by('pk').reverse()[0]
    d:Developer = Developer.objects.get(user=request.user)
    tm = d.team.all()[0]
    devs = Developer.objects.all().filter(team=tm)
    task_owner: Developer = mt.owner
    if mt.team != tm:
        return redirect('team_view')
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment:Comment = form.save(commit=False)
            comment.owner = request.user
            comment.mastertask = mt 
            comment.task = t 
            if mt.owner == d and mt.status == 3 and request.POST['approve'] == "Update":
                Vote.objects.all().filter(task=t).filter(status=mt.status).delete() 
                saveLog(mt, "Task is updated by"+ str(d) + ".")
            if len(Vote.objects.all().filter(task=t).filter(status=mt.status).filter(owner=d)) == 0:
                if request.POST['approve'] == "Yes":
                    comment.approved = True 
                    vote = Vote()
                    vote.owner = d
                    vote.task = t 
                    vote.status = mt.status
                    vote.vote = True 
                    vote.save()
                    
                    subject = 'TPS:Notification || The task you created has received an approve vote.'
                    contentList = [
                        'Your task called ' + t.title + ' has received an aprove vote.',
                        'Approver: ' + str(d),
                        str(d) + '\'s comment: ' + comment.body,
                        'Priority: ' + t.getPriority(),
                        'Due date: ' + str(t.promised_date)
                    ]

                    url = request._current_scheme_host + "/tasks/" + str(t.masterTask_id)
                    html_message = render_to_string('tasks/email_template.html',
                    {'title': 'A task has received an approve vote!', 'contentList': contentList, 'url': url, 'background_color': '#5cb85c'})

                    plain_message = strip_tags(html_message)
                    from_email = 'no-reply@tps.info.tr'

                    send_mail(subject, plain_message, from_email, [task_owner.user.email], html_message=html_message)
                    saveLog(mt, "Task received an approve vote by "+ str(d) + ".")
                elif request.POST['approve'] == "No":
                    comment.approved = False
                    vote = Vote()
                    vote.owner = d
                    vote.task = t 
                    vote.status = mt.status 
                    vote.vote = False 
                    vote.save()

                    subject = 'TPS:Notification || The task you created has received a revision request.'
                    contentList = [
                        'Your task called ' + t.title + ' has received a revision request.',
                        'Requested by: ' + str(d),
                        str(d) + '\'s comment: ' + comment.body,
                        'Priority: ' + t.getPriority(),
                        'Due date: ' + str(t.promised_date)
                    ]
                    url = request._current_scheme_host + "/tasks/" + str(t.masterTask_id)
                    html_message = render_to_string('tasks/email_template.html',
                    {'title':'A task has received a revision request.', 'contentList': contentList, 'url':url, 'background_color': '#ff2400'})

                    plain_message = strip_tags(html_message)
                    from_email = 'no-reply@tps.info.tr'

                    send_mail(subject, plain_message, from_email, [task_owner.user.email], html_message=html_message)
                    saveLog(mt, "Task received a revision request by "+ str(d) + ".")
            comment.save()
            return redirect('view_task', task_id)
    form = CommentForm()
    comments = Comment.objects.all().filter(mastertask=mt).order_by('date').reverse()
    voted = len(Vote.objects.all().filter(task=t).filter(status=mt.status).filter(owner=d))
    v_app = len(Vote.objects.all().filter(task=t).filter(status=mt.status).filter(vote=True))
    v_den = len(Vote.objects.all().filter(task=t).filter(status=mt.status).filter(vote=False))
    reopen = False 
    if mt.status == 1 and v_app > len(mt.team.developer_set.all())/2 :
        mt.status = 2
        mt.save()
        
        subject = 'TPS:Notification || The task you created is now in open state.'

        contentList = [
            'Your task called ' + t.title + ' is now in open state.',
            'Description: ' + t.description,
            'Priority: ' + t.getPriority(),
            'Due date: ' + str(t.promised_date)
        ]
        
        url = request._current_scheme_host + "/tasks/" + str(t.masterTask_id)

        html_message = render_to_string('tasks/email_template.html',           
         {'title':'Your task is now in open state!','contentList': contentList, 'url':url, 'background_color': '#003399'})

        plain_message = strip_tags(html_message)
        from_email = 'no-reply@tps.info.tr'

        send_mail(subject, plain_message, from_email, [task_owner.user.email], html_message=html_message)
        saveLog(mt, "All approved. Task is now in open state.")
    elif mt.status == 3 and v_app > len(mt.team.developer_set.all())/2 :
        mt.status = 5
        mt.save()

        subject = 'TPS:Notification || The task you created is now accepted.'
        url = request._current_scheme_host + "/tasks/" + str(t.masterTask_id)

        html_message = render_to_string('tasks/email_template.html',           
         {'title':'Your task is accepted!', 'contentList': ['Your task called ' + t.title + ' is now accepted.'],'url':url, 'background_color': '#003399' })

        plain_message = strip_tags(html_message)
        from_email = 'no-reply@tps.info.tr'

        send_mail(subject, plain_message, from_email, [task_owner.user.email], html_message=html_message)
        saveLog(mt, "All approved. Task is now accepted!")
    elif mt.status == 3 and v_den >= len(mt.team.developer_set.all())/2 :
        reopen = True 
        
    try:
        liked = Like.objects.get(owner = d, mastertask = mt).liked
    except ObjectDoesNotExist:
        liked = None 

    logs = MasterTaskLog.objects.all().filter(mastertask=mt).filter(gizli=False).order_by('tarih').reverse()

    context = {
        'page_title': 'View Task',
        'mastertask': mt,
        'task': t, 
        'tp': mt.difficulty * t.priority,
        'form': form,
        'voted': voted,
        'mytask': mt.owner == d,
        'v_app': v_app,
        'v_den': v_den,
        'reopen': reopen, 
        'liked': liked, 
        'comments': comments,
        'logs' : logs
    }
    return render(request, "tasks/task_view.html", context)


@login_required
@permission_required('tasks.add_developer')  # students don't have the right to do so... 
def lecturer_view(request):
    l:Lecturer = Lecturer.objects.get(user=request.user)
    mcourses = MasterCourse.objects.all()
    courses = Course.objects.all().filter(lecturer = l).order_by('pk').reverse()
    context = {
        'page_title': 'Home', 
        'courses': courses,
        'mcourses': mcourses
    }
    return render(request, 'tasks/lecturer_index.html', context) 

def tpslogin(request):
    if request.method == 'POST':
        userid = request.POST['universityid']
        pwd = request.POST['tpspass']

        user = authenticate(request, username=userid, password=pwd)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            context = {
                'page_title': 'Login',
                'login_error': 'Login failed. Please contact Kaya Oğuz (kaya.oguz@ieu.edu.tr) if you are experiencing problems logging in.'
                }
            return render(request, 'tasks/login.html', context)
    else: 
        context = {
            'page_title': 'Login'
        }
        return render(request, 'tasks/login.html', context)

def tpslogout(request):
    logout(request)
    return redirect('index')

@login_required
def profile (request):
    return render(request, 'tasks/profile.html', {'page_title': 'Profile' })


@login_required
def my_details (request):
    return render(request, 'tasks/my_details.html', {'page_title': 'My Details' })

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return render(request, 'tasks/password_success.html', {
                'page_title': 'Password changed.'
            })
        else:
            return render(
                request,
                'tasks/password.html',
                {
                    'page_title': 'Change Password',
                    'form': form,
                    'pass_error': 'Failed. Password not changed.'
                }
            ) 
    else:
        form = PasswordChangeForm(request.user)
        return render(request, 'tasks/change_password.html', {'page_title': 'Change Password', 'form': form })

@login_required
def my_teams (request):
    return render(request, 'tasks/my_teams.html', {'page_title': 'My Details' })

@login_required
def my_email (request):
 
        return render(request, 'tasks/my_email.html', {'page_title': 'Change Password'})


@login_required
def my_notifications (request):
    return render(request, 'tasks/my_notifications.html', {'page_title': 'My Details' })

@login_required
@permission_required('tasks.add_mastercourse')
def create_master_course(request):
    if request.method == 'POST':
        form = MasterCourseForm(request.POST)
        form_details = CourseForm(request.POST)
        if form.is_valid() and form_details.is_valid():
            mastercourse = form.save()
            course:Course = form_details.save(commit=False)
            course.masterCourse = mastercourse
            course.lecturer = Lecturer.objects.get(user=request.user)
            course.save() 
            return redirect('lecturer_view')
    else: 
        form = MasterCourseForm()
        form_details = CourseForm()
    
    return render(request, 'tasks/mastercourse_create.html', {
        'page_title': 'Create New Master Course',
        'form': form,
        'form_details': form_details
    })

@login_required
@permission_required('tasks.add_team')
@permission_required('tasks.add_developer')
def create_team(request, course_id):
    if request.method == 'POST':
        from random import shuffle # only needed here... 
        stdlist = request.POST["stdlist"].split('\r\n')
        shuffle(stdlist)

        cid = int(request.POST["course_id"])
        course = Course.objects.get(pk=cid)
        lecturer = Lecturer.objects.get(user=request.user)

        team_size = int(request.POST["team_size"])
        team_no = 1
        team_std_count = 0
        teams = dict()
        steams = list() 
        for std in stdlist:
            team_name = "Team " + str(team_no)
            if team_name not in teams:
                teams[team_name] = list() 
                team_std_count = 0
                team = Team() 
                team.course = course 
                team.name = team_name 
                team.github = "ENTER YOUR GIT REP ADDRESS HERE"
                team.supervisor = lecturer 
                team.save()
                steams.append(team)
            
            fields = std.split('\t')
            uniId = fields[1].strip()
            fullname = fields[2].strip() + " " + fields[3].strip()
            teams[team_name].append([uniId, fullname])
            team_std_count += 1 
            if team_std_count == team_size:
                team_no += 1
            
            # add to team 
            user = User.objects.create_user(uniId, None, uniId)
            user.first_name = fields[2].strip()
            user.last_name = fields[3].strip()
            group = Group.objects.get(name="student")
            user.groups.add(group)
            user.save()
            d = Developer()
            d.user = user 
            d.save()
            d.team.add(steams[-1])
            d.save()
        
        return render(request, 'tasks/team_success.html', {
            'page_title': 'Results',
            'teams': teams
        })
    else: 
    # provide a text area for student names
        course = Course.objects.get(pk=course_id)
        return render(request, 'tasks/team_create.html', {
            'page_title': 'Create Teams',
            'course': course
        })
    
@login_required
@permission_required('tasks.add_team')
def lecturer_course_view(request, course_id):
    course = Course.objects.get(pk=course_id)
    milestones = course.milestone_set.all()
    teams = course.team_set.all()
    tasks = list()
    for team in teams:
        for task in team.mastertask_set.all().order_by('pk').reverse():
            tasks.append(task)
    context = {
        'page_title': 'Lecturer Course View',
        'course': course,
        'teams': teams,
        'milestones': milestones,
        'tasks': tasks 
    }

    return render(request, 'tasks/lecturer_course_view.html', context)

@login_required
@permission_required('tasks.add_team')
def lecturer_team_view(request, team_id):
    team = Team.objects.get(pk=team_id)
    devs = team.developer_set.all()
    tasks = team.mastertask_set.all().order_by('pk').reverse()
    context = {
        'page_title': 'Lecturer Team View',
        'team': team,
        'course': team.course, 
        'devs': devs, 
        'tasks': tasks 
    }

    return render(request, 'tasks/lecturer_team_view.html', context)


@login_required 
@permission_required('tasks.add_milestone')
def lecturer_create_milestone(request, course_id):
    course = Course.objects.get(pk=course_id)
    if request.method == 'POST':
        form = MilestoneForm(request.POST)
        if form.is_valid():
            milestone:Milestone = form.save(commit=False)
            milestone.course = course 
            milestone.save() 
            return redirect('lecturer_view_course', course_id)
    form = MilestoneForm
    context = {
        'page_title': 'Create New Milestone',
        'course': course, 
        'form': form 
    }
    return render(request, "tasks/milestone_create.html", context)

@login_required
@permission_required('tasks.add_milestone')
def lecturer_grade_milestone(request, milestone_id):
    milestone:Milestone = Milestone.objects.get(pk=milestone_id)
    course:Course = milestone.course
    teams = course.team_set.all() 
    if request.method == 'POST':
        for team in teams:
            # print(team.name + '->' + request.POST['grade['+ str(team.pk) +']'])
            q:TeamMilestoneGrade = TeamMilestoneGrade.objects.all().filter(team=team).filter(milestone=milestone)
            if len(q) == 0:
                tp:TeamMilestoneGrade = TeamMilestoneGrade()
                tp.milestone = milestone 
                tp.team = team 
                tp.grade = request.POST['grade[' + str(team.pk) + ']']
                tp.save() 
            else:
                q[0].grade = request.POST['grade[' + str(team.pk) + ']']
                q[0].save()
        return redirect('lecturer_view_course', course.pk)        
    grades = dict()
    for team in teams: 
        q:TeamMilestoneGrade = TeamMilestoneGrade.objects.all().filter(team=team).filter(milestone=milestone)
        if len(q) == 0:
            grades[team.name] = [team.pk, 0]
        else:
            grades[team.name] = [team.pk, q[0].grade]
    context = {
        'page_title': 'Update Grades',
        'milestone': milestone, 
        'course': course, 
        'teams': teams, 
        'grades': grades 
    }
    return render(request, "tasks/milestone_grade.html", context) 

@login_required 
@permission_required('tasks.add_milestone')
def lecturer_edit_milestone(request, milestone_id):
    milestone:Milestone = Milestone.objects.get(pk=milestone_id)
    if request.method == 'POST':
        form = MilestoneForm(request.POST)
        if form.is_valid():
            mform:Milestone = form.save(commit=False)
            mform.course = milestone.course
            mform.pk = milestone.pk
            mform.save() 
            return redirect('lecturer_view_course', mform.course.pk)
    form = MilestoneForm(instance=milestone)
    context = {
        'page_title': 'Edit Milestone',
        'milestone': milestone,
        'form': form 
    }
    return render(request, "tasks/milestone_edit.html", context)


@login_required
@permission_required('tasks.add_team')
def lecturer_task_view(request, task_id):
    mt:MasterTask = MasterTask.objects.get(pk=task_id)
    t:Task = Task.objects.all().filter(masterTask=mt).order_by('pk').reverse()[0]
    course = mt.team.course 

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment:Comment = form.save(commit=False)
            comment.owner = request.user 
            comment.mastertask = mt 
            comment.task = t 
            comment.save()
            return redirect('lecturer_view_task', task_id)
    form = CommentForm()
    comments = Comment.objects.all().filter(mastertask=mt).order_by('date').reverse()
    v_app = len(Vote.objects.all().filter(task=t).filter(status=mt.status).filter(vote=True))
    v_den = len(Vote.objects.all().filter(task=t).filter(status=mt.status).filter(vote=False))
    if mt.status == 1 and v_app > len(mt.team.developer_set.all())/2 :
        mt.status = 2
        mt.save()
    elif mt.status == 3 and v_app > len(mt.team.developer_set.all())/2 :
        mt.status = 5
        mt.save()

    logs = MasterTaskLog.objects.all().filter(mastertask=mt).order_by('tarih').reverse()

    context = {
        'page_title': 'Lecturer Task View',
        'mastertask': mt,
        'task': t, 
        'tp': mt.difficulty * t.priority,
        'form': form,
        'v_app': v_app,
        'v_den': v_den,
        'comments': comments,
        'course': course, 
        'logs': logs 
    }
    return render(request, "tasks/lecturer_task_view.html", context)