from allauth.account.views import SignupView

from .forms import UserSignupForm


class UserSignupView(SignupView):
    form_class = UserSignupForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs
