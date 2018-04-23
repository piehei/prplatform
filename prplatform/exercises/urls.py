from django.urls import path
from django.conf.urls import url

from . import views

app_name = "exercises"
urlpatterns = [
    path('', view=views.ExerciseListView.as_view(), name="exercise-list"),
    path('<int:pk>/', view=views.ExerciseDetailView.as_view(), name="detail"),
    path('create/', view=views.ExerciseCreateView.as_view(), name="create")
]
