import json

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.http import Http404, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView, TemplateView, UpdateView, View

from prm.core.services import CacheService, MetamaskService
from prm.users.services import recalculate_user_balance, set_parent_in_smart

from .forms import AvatarUpdateForm, BuyTokenForm, ProfileUserUpdateForm

User = get_user_model()


def metamask_confirm(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user = get_object_or_404(User, username=data.get("user"))
            account_address = data.get("accountAddress")
            signature = data.get("signature")
            csrf_token = data.get("csrf_token")
            # verify signature
            is_valid_signature = MetamaskService.verify_signature(
                account_address=account_address,
                signature=signature,
                original_message=csrf_token,
            )
            if not is_valid_signature:
                return JsonResponse({"error": "Invalid signature"}, status=400)
            # update user metamask data
            MetamaskService.confirm_user_wallet(
                user=user, account_address=account_address
            )

            if user.parent:
                set_parent_in_smart(user)
            recalculate_user_balance(user)
        except Exception as e:
            return JsonResponse({"message": "Error", "exception": str(e)}, status=500)
        return JsonResponse({"message": "Success"})
    return HttpResponseNotAllowed(["POST"])


class PollToken(LoginRequiredMixin, TemplateView):
    def get_context_data(self, *args, **kwargs):
        token = CacheService.get_token()
        token_active_round = CacheService.get_token_active_round()
        token_rounds = CacheService.get_token_rounds()
        return {
            "token": token,
            "token_active_round": token_active_round,
            "token_rounds": token_rounds,
        }

    def get(self, request, *args, **kwargs):
        template_name = "dashboard/components/token_active_round.html"
        if request.path == reverse_lazy("dashboard:poll_token_rounds"):
            template_name = "dashboard/components/token_rounds.html"
        context = self.get_context_data()
        return render(request, template_name, context)


class PollUserBalance(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/components/user_balance.html"

    def get_context_data(self, *args, **kwargs):
        user = self.request.user
        token = CacheService.get_token()
        token_active_round = CacheService.get_token_active_round()
        user_balance = CacheService.get_user_balance(user, token)
        return {
            "user": user,
            "user_balance": user_balance,
            "token": token,
            "token_active_round": token_active_round,
        }


class PollUserTransactions(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/components/transaction_history.html"

    def get_context_data(self, *args, **kwargs):
        transactions = CacheService.get_user_transactions(self.request.user)
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
    default_limit = 10
    default_page = 1
    max_limit = 50

    def get_context_data(self):
        token = CacheService.get_token()
        token_rounds = CacheService.get_token_rounds()
        token_active_round = cache.get("token_active_round")
        user = self.request.user
        user_referral = self.request.build_absolute_uri(
            reverse_lazy("account_signup") + "?referral=" + user.username
        )
        user_balance = CacheService.get_user_balance(user, token)
        user_children = CacheService.get_user_children(user)
        user_transactions = CacheService.get_user_transactions(user)

        # Children pagination
        page_sizes = [10, 25, 50]
        page_size = self.request.COOKIES.get("children_size", self.default_limit)
        page_num = self.request.GET.get("page", self.default_page)
        user_children = Paginator(user_children, page_size).page(page_num)
        user_children_page_range = user_children.paginator.get_elided_page_range(
            page_num, on_each_side=3, on_ends=1
        )
        # Transactions pagination
        user_transactions = Paginator(user_transactions, page_size).page(page_num)
        user_transactions_page_range = (
            user_transactions.paginator.get_elided_page_range(
                page_num, on_each_side=3, on_ends=1
            )
        )

        return {
            "user": user,
            "user_referral_link": user_referral,
            "user_balance": user_balance,
            "user_children": user_children,
            "user_children_page_range": user_children_page_range,
            "user_transactions": user_transactions,
            "user_transactions_page_range": user_transactions_page_range,
            "token": token,
            "token_rounds": token_rounds,
            "token_active_round": token_active_round,
            "page_sizes": page_sizes,
        }

    def get(self, request, *args, **kwargs):
        try:
            context = self.get_context_data()
        except (EmptyPage, InvalidPage):
            raise Http404()
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
