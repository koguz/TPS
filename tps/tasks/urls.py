from django.urls import path

from . import views 

urlpatterns = [
    path('', views.index, name='index'),
    path('updates/', views.update_view, name='view_updates'),
    path('lecturer/', views.lecturer_view, name='lecturer_view'),
    path('lecturer/course/<int:course_id>/', views.lecturer_course_view, name='lecturer_view_course'),
    path('lecturer/team/<int:team_id>/', views.lecturer_team_view, name='lecturer_view_team'),
    path('lecturer/task/<int:task_id>/', views.lecturer_task_view, name='lecturer_view_task'),
    path('courses/create/', views.create_master_course, name='create_mastercourse'),
    path('courses/<int:course_id>/milestone/create/', views.lecturer_create_milestone, name='create_milestone'),
    path('courses/milestone/<int:milestone_id>/edit/', views.lecturer_edit_milestone, name='edit_milestone'),
    path('courses/milestone/<int:milestone_id>/grade/', views.lecturer_grade_milestone, name='grade_milestone'),
    path('team/', views.team_view, name='team_view'),
    path('team/edit/', views.edit_team, name='edit_team'),
    path('team/create/<int:course_id>/', views.create_team, name='create_team'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/', views.view_task, name='view_task'),
    path('tasks/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('tasks/<int:task_id>/complete/', views.complete_task, name='complete_task'),
    path('tasks/<int:task_id>/liked/<int:liked>/', views.like_task, name='like_task'),
    path('accounts/login/', views.tpslogin, name='login'),
    path('accounts/logout/', views.tpslogout, name='logout'),
    path('accounts/change-password/', views.change_password, name='change_password')
]
