import json

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView, TemplateView, UpdateView, View

from prm.core.selectors import get_token, get_token_rounds, get_user_transactions
from prm.core.services import create_transaction
from prm.core.utils import calculate_rounded_total_price
from prm.users.services import recalculate_user_balance, set_parent_in_smart

from .forms import AvatarUpdateForm, BuyTokenForm, ProfileUserUpdateForm

User = get_user_model()


def metamask_confirm(request):
    if request.method == "POST":
        data = json.loads(request.body)
        account_address = data.get("accountAddress")
        user = get_object_or_404(User, username=data.get("user"))

        if not account_address:
            return HttpResponseBadRequest()

        user.confirm_metamask(account_address)
        if user.parent:
            set_parent_in_smart(user)
        recalculate_user_balance(user)
        
        return JsonResponse({"message": "Success"})
    return HttpResponseNotAllowed(["POST"])


class PollUserBalance(TemplateView):
    template_name = "dashboard/components/user_balance.html"

    def get_context_data(self, *args, **kwargs):
        user = self.request.user
        token = get_token()
        user_balance = calculate_rounded_total_price(
            unit_price=user.token_balance,
            amount=token.active_round.unit_price,
        )
        return {"user": user, "user_balance": user_balance, "token": token}


class PollTokenActiveRound(TemplateView):
    template_name = "dashboard/components/token_active_round.html"

    def get_context_data(self, *args, **kwargs):
        return {"token": get_token()}


class PollTokenRounds(TemplateView):
    template_name = "dashboard/components/token_rounds.html"

    def get_context_data(self, *args, **kwargs):
        return {"token": get_token(), "token_rounds": get_token_rounds()}


class PollUserTransactions(TemplateView):
    template_name = "dashboard/components/transaction_history.html"

    def get_context_data(self, *args, **kwargs):
        user = self.request.user
        transactions = get_user_transactions(user=user)
        return {"user_transactions": transactions}


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
        token = get_token()
        token_rounds = get_token_rounds()
        user = self.request.user
        user_referral = self.request.build_absolute_uri(
            reverse_lazy("account_signup") + "?referral=" + user.username
        )
        user_balance = calculate_rounded_total_price(
            unit_price=user.token_balance,
            amount=token.active_round.unit_price,
        )
        user_transactions = get_user_transactions(user=user)
        user_children = user.children.select_related("settings")
        return {
            "user": user,
            "user_referral_link": user_referral,
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
            user = self.request.user
            token_amount = form.cleaned_data["token_amount"]

            create_transaction(buyer=user, token_amount=token_amount)
            user.update_token_balance(token_amount)

            return redirect(
                reverse_lazy("dashboard:token", kwargs={"username": user.username})
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
