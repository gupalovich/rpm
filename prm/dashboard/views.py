from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView, UpdateView, View

from prm.core.services import create_transaction
from prm.core.utils import calculate_rounded_total_price
from prm.tokens.models import Token, TokenRound, TokenTransaction

from .forms import AvatarUpdateForm, BuyTokenForm, ProfileUserUpdateForm

User = get_user_model()


class DashboardRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse_lazy(
                "dashboard:index", kwargs={"username": self.request.user.username}
            )
        return reverse_lazy("account_login")


class DashboardBaseView(LoginRequiredMixin, View):
    template_name = ""

    def get_context_data(self):
        token = Token.objects.first()
        token_rounds = TokenRound.objects.all()
        user = self.request.user
        user_balance = calculate_rounded_total_price(
            unit_price=user.token_balance,
            amount=token.active_round.unit_price,
        )
        user_transactions = TokenTransaction.objects.select_related("buyer").filter(
            Q(buyer=user) | Q(buyer__parent=user, reward_sent=True)
        )
        user_children = user.children.select_related("settings")
        return {
            "user": user,
            "user_balance": user_balance,
            "user_transactions": user_transactions,
            "user_children": user_children,
            "token": token,
            "token_rounds": token_rounds,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)


class DashboardIndexView(DashboardBaseView):
    template_name = "dashboard/index.html"


class DashboardTokenView(DashboardBaseView):
    template_name = "dashboard/token.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context["buy_token_form"] = BuyTokenForm()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = BuyTokenForm(request.POST)
        if form.is_valid():
            token_amount = form.cleaned_data["token_amount"]

            create_transaction(buyer=self.request.user, token_amount=token_amount)

            return redirect(
                reverse_lazy(
                    "dashboard:token", kwargs={"username": self.request.user.username}
                )
            )
        context = self.get_context_data()
        context["buy_token_form"] = form
        return render(request, self.template_name, context)


class DashboardTeamView(DashboardBaseView):
    template_name = "dashboard/team.html"


class DashboardProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileUserUpdateForm
    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = "dashboard/profile.html"
    success_message = _("Информация успешно обновлена")

    def get_success_url(self):
        return reverse_lazy(
            "dashboard:profile", kwargs={"username": self.request.user.username}
        )

    def get_object(self, *args, **kwargs):
        return self.request.user


class AvatarUpdateView(LoginRequiredMixin, View):
    def post(self, request):
        form = AvatarUpdateForm(request.POST, request.FILES)
        if form.is_valid() and request.FILES:
            user = self.request.user
            user.avatar = form.cleaned_data.get("avatar")
            user.save()
            return JsonResponse({"avatar_url": user.avatar.url})
        # handle form errors
        errors = form.errors.as_data()
        error_messages = [
            error.message for error_list in errors.values() for error in error_list
        ]
        return JsonResponse({"error": error_messages}, status=400)
