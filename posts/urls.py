from django.urls import path
from rest_framework.authtoken import views as rest_views

from . import views

urlpatterns = [
    path('api-token-auth/', rest_views.obtain_auth_token),
    path('api/v1/posts/<int:id>/', views.APIPostDetail.as_view()),
    path('api/v1/posts/', views.APIPost.as_view()),
    path("follow/", views.follow_index, name="follow_index"),
    path("<str:username>/follow/", views.profile_follow, name="profile_follow"),
    path("<str:username>/unfollow/",
         views.profile_unfollow, name="profile_unfollow"),
    path("group/<slug>/", views.group_posts, name="group_posts"),
    path("new/", views.new_post, name="new_post"),
    path("", views.index, name="index"),
    path('<str:username>/', views.profile, name='profile'),
    path('<str:username>/<int:post_id>/', views.post_view, name='post_view'),
    path(
        '<str:username>/<int:post_id>/edit/',
        views.post_edit,
        name='post_edit'
    ),
    path("<username>/<int:post_id>/comment",
         views.add_comment, name="add_comment")
]
