from django.urls import path
from . import views

urlpatterns = [
    path("", views.todo_list, name="todo_list"),
    
    path("completed/<int:todo_id>", views.completed_todo, name="completed_todo"),
    
]