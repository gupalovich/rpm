# from django.contrib.messages.views import SuccessMessageMixin
# from django.http import JsonResponse
# from .forms import AvatarUpdateForm, CustomUserUpdateForm
# from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, RedirectView, View

User = get_user_model()


class HomeRedirectView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect(
                reverse("dashboard:index", kwargs={"username": request.user.username}),
                permanent=False,
            )
        return redirect(reverse("account_login"), permanent=False)


class DashboardRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            "dashboard:index", kwargs={"username": self.request.user.username}
        )


class DashboardIndexView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = "dashboard/index.html"


class DashboardTokenView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = "dashboard/token.html"


class DashboardTeamView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = "dashboard/team.html"


class DashboardProfileView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = "dashboard/profile.html"


# class DashboardSettingsView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
#     form_class = CustomUserUpdateForm
#     template_name = "dashboard/settings.html"
#     success_message = _("Information successfully updated")

#     def get_success_url(self):
#         return reverse("dashboard:settings")

#     def get_object(self, *args, **kwargs):
#         return self.request.user


# class AvatarUpdateView(View):
#     def post(self, request):
#         form = AvatarUpdateForm(request.POST, request.FILES)
#         if form.is_valid() and request.FILES:
#             user = self.request.user
#             user.avatar = form.cleaned_data.get("avatar")
#             user.save()
#             return JsonResponse({"avatar_url": user.avatar.url})
#         # handle form errors
#         errors = form.errors.as_data()
#         error_messages = [
#             error.message for error_list in errors.values() for error in error_list
#         ]
#         return JsonResponse({"error": error_messages}, status=400)
