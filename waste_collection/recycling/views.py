from django.views import View
import calendar
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import WasteCollection
from .forms import WasteCollectionForm


# ------------------------------------------------------------
# ROLE HELPERS
#
# Two roles are required by the spec: "admin" and "user".
# We use Django's built-in is_staff flag to represent "admin"
# (this is what the admin site already uses), so no extra role
# field is needed. Everyone else is a normal resident ("user").
# ------------------------------------------------------------
def is_admin(user):
    return user.is_authenticated and user.is_staff


# ------------------------------
# HOME VIEW – Public landing page
# Shown to everyone at "/". Logged-in users get a quick-glance
# dashboard (their own stats + recent requests, or every request
# for admins); logged-out visitors get a marketing/"how it works"
# page with signup/login calls to action.
# ------------------------------
class HomeView(TemplateView):
    template_name = 'recycling/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['waste_types'] = WasteCollection.WASTE_TYPES

        if user.is_authenticated:
            admin = is_admin(user)
            qs = WasteCollection.objects.all()
            if not admin:
                qs = qs.filter(requested_by=user)

            context['is_admin'] = admin
            context['total_count'] = qs.count()
            context['submitted_count'] = qs.filter(status='submitted').count()
            context['pending_count'] = qs.filter(status='pending').count()
            context['collected_count'] = qs.filter(status='collected').count()
            context['completed_count'] = qs.filter(status='completed').count()
            context['recent_collections'] = qs[:5]

        return context


# ------------------------------
# AUTH VIEWS – Signup / Login / Logout
# ------------------------------
class SignUpView(CreateView):
    """Lets a resident create a 'user' account (not staff/admin)."""
    form_class = UserCreationForm
    template_name = 'recycling/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Account created. Please log in.")
        return response


class CollectionLoginView(LoginView):
    template_name = 'recycling/login.html'


class CollectionLogoutView(LogoutView):
    next_page = 'login'


# ------------------------------
# LIST VIEW – Show collections
# Admins see every non-archived request. Regular users only see
# their own requests (archived or not - archiving only hides a
# record from the admin's active list, it never affects what a
# resident can see in their own history).
# ------------------------------
class CollectionListView(LoginRequiredMixin, ListView):
    model = WasteCollection
    template_name = 'recycling/collection_list.html'
    context_object_name = 'collections'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if is_admin(self.request.user):
            return qs.filter(archived=False)
        return qs.filter(requested_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        return context


# ------------------------------
# DETAIL VIEW – Show a single collection record
# A regular user may only view their own record.
# ------------------------------
class CollectionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = WasteCollection
    template_name = 'recycling/collection_detail.html'
    context_object_name = 'collection'

    def test_func(self):
        obj = self.get_object()
        return is_admin(self.request.user) or obj.requested_by_id == self.request.user.id

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        return context


# ------------------------------
# CREATE VIEW – Add a new collection entry
# Any logged-in resident can request a collection; it is
# automatically tied to their account and always starts life as
# "Submitted for Collection" - nobody picks a status here.
# Admins do not create requests - they only manage existing ones.
# ------------------------------
class CollectionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = WasteCollection
    form_class = WasteCollectionForm
    template_name = 'recycling/collection_form.html'
    success_url = reverse_lazy('collection_list')

    def test_func(self):
        return not is_admin(self.request.user)

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        form.instance.status = 'submitted'
        return super().form_valid(form)


# ------------------------------
# UPDATE VIEW – Edit an existing collection entry
# Regular users may edit only their own (not-yet-collected) request,
# but still cannot touch the status. Admins may edit any record and
# can additionally move it through pending -> collected -> completed.
# ------------------------------
class CollectionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = WasteCollection
    form_class = WasteCollectionForm
    template_name = 'recycling/collection_form.html'
    success_url = reverse_lazy('collection_list')

    def test_func(self):
        obj = self.get_object()
        return is_admin(self.request.user) or obj.requested_by_id == self.request.user.id

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_admin'] = is_admin(self.request.user)
        return kwargs


# ------------------------------
# DELETE VIEW – Confirm and delete a collection entry
#
# Admins "deleting" a record only archives it - the row is never
# destroyed, so residents still see the full record in their own
# history. Residents deleting their own request (only while it's
# still 'submitted') still does a real, permanent delete - there's
# nothing to preserve for a request that was never accepted.
# ------------------------------
class CollectionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = WasteCollection
    template_name = 'recycling/collection_confirm_delete.html'
    success_url = reverse_lazy('collection_list')

    def test_func(self):
        obj = self.get_object()
        if is_admin(self.request.user):
            return True
        return obj.requested_by_id == self.request.user.id and obj.status == 'submitted'

    def post(self, request, *args, **kwargs):
        # NOTE: Django 4.0+ no longer routes deletion through delete() -
        # DeleteView now handles POST via form_valid()/post() internally.
        # Overriding post() directly keeps this working across versions.
        self.object = self.get_object()
        if is_admin(request.user):
            self.object.archived = True
            self.object.save(update_fields=['archived'])
            messages.success(request, "Collection archived from your view.")
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)


# ------------------------------
# ADMIN TOOL – Bulk-archive completed collections for a chosen month.
# Archived records disappear from the admin's active list, but the
# underlying row is never deleted, so residents still see them in
# their own collection history.
# ------------------------------
class ArchiveCompletedByMonthView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return is_admin(self.request.user)

    def post(self, request, *args, **kwargs):
        month_str = request.POST.get('month')  # 'YYYY-MM' from <input type="month">
        try:
            year, month = map(int, month_str.split('-'))
        except (ValueError, AttributeError, TypeError):
            messages.error(request, "Please choose a valid month.")
            return redirect('collection_list')

        count = WasteCollection.objects.filter(
            status='completed',
            collection_date__year=year,
            collection_date__month=month,
            archived=False,
        ).update(archived=True)

        messages.success(
            request,
            f"Archived {count} completed collection(s) for {calendar.month_name[month]} {year}."
        )
        return redirect('collection_list')