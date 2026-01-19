from django.shortcuts import render,redirect

# Create your views here.
from .models import Todo
def todo_list(request):
    todos=Todo.objects.all()
    
    if request.method=="POST":
        task_name=request.POST.get("task_name")
        if task_name:
            Todo.objects.create(title=task_name)
        return redirect("todo_list")
    
    return render(request, "myapp/todo_list.html", {"todolist":todos})


        
def completed_todo(request,todo_id):
    todo=Todo.objects.get(id=todo_id)
    todo.completed=True
    todo.save()
    return redirect("todo_list")