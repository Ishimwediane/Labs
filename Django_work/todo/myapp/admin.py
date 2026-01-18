from django.contrib import admin

# Register your models here.
from .models import Todo

admin.site.register(Todo) #to see our todo in admin for add ,edit or delete todos there