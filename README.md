# ♻️ Waste Collection Management System

A full-stack Django web application for scheduling and tracking household waste collection requests.

---

## 1. Use Case

**Who is this for?**
Small municipal waste-management contractors (or a community recycling co-op) who currently track household collection requests on paper or in spreadsheets, and want a simple web system to replace that process.

**The problem:**
Residents call or message the depot to request a waste pickup. Staff manually write down the household, address, waste type, and date, then have to phone around to confirm status. There's no shared, searchable record, and no way for a resident to check on their own request without calling in.

**The solution:**
A Django web app with two roles:

- **Resident ("user" role)** — can sign up, log in, and:
  - Submit a new waste collection request (household name, address, phone, waste type, estimated weight, preferred date, notes)
  - Pick a waste type from six clickable image cards (Plastic, Paper, Glass, Metal, Organic, Electronic) instead of a plain dropdown
  - View a personal dashboard on the home page with counts of their own requests by status
  - View a list of only *their own* requests
  - Edit their own requests, or cancel (permanently delete) a request while it is still `Submitted for Collection`
- **Depot staff ("admin" role, `is_staff=True`)** — can:
  - View *all* collection requests from every resident, with the requester's username shown
  - Move any request forward through its status workflow (`Submitted → Pending Pickup → Collected → Completed`)
  - Edit any record
  - **Archive** (soft-delete) a completed record — this removes it from the admin's active list, but the original resident can still see it in their own history, since the underlying record is never destroyed
  - Bulk-archive every `Completed` request for a chosen month in one click
  - Cannot create new collection requests — that action is resident-only, both hidden in the UI and blocked at the view level
  - Use the Django admin site for bulk search, filtering by waste type/status, and date-hierarchy drill-down

**Why it matters:** residents get visibility into their own requests without calling the depot, and staff get one authoritative, filterable record — plus a way to keep their working list tidy without ever losing a resident's history — instead of scattered notes and irreversible deletions.

---

## 2. Tech Design

**Stack:** Django (project scaffolded on 5.2.8, currently running 6.1.1), SQLite (dev database), server-rendered HTML/CSS (no JS framework needed for CRUD; a small vanilla-JS snippet syncs the waste-type card UI with its underlying radio input).

**High-level architecture:**

```
Browser
   │
   ▼
Django URLconf (waste_collection/urls.py)
   │
   ▼
recycling app
   ├── models.py   → WasteCollection (data)
   ├── forms.py    → WasteCollectionForm (validation, radio-card widget, admin-only status field)
   ├── views.py    → Class-based views (Home/List/Detail/Create/Update/Delete/Archive + Auth)
   ├── admin.py    → Django admin registration for staff bulk management
   ├── static/
   │   ├── css/style.css
   │   └── waste/images/{plastic,paper,glass,metal,organic,electronic}.svg
   └── templates/recycling/  → base.html + home/list/detail/form/delete templates
   │
   ▼
SQLite database
```

> **Static files note:** app-level static assets live at `recycling/static/...` (lowercase — required for Django's `AppDirectoriesFinder` to discover them, and for portability to case-sensitive deployment filesystems). Templates reference them with `{% static 'waste/images/plastic.svg' %}` etc. — note the folder order is `waste/images/`, not `images/waste/`.

**Data model — `WasteCollection`:**

| Field | Type | Notes |
|---|---|---|
| household_name | CharField | required |
| address | TextField | required |
| phone | CharField | required |
| waste_type | CharField (choices) | `plastic` / `paper` / `glass` / `metal` / `organic` / `electronic` — rendered as image-card radio buttons |
| weight_kg | DecimalField | |
| collection_date | DateField | defaults to today |
| status | CharField (choices) | `submitted` / `pending` / `collected` / `completed` — see workflow below |
| notes | TextField | optional |
| **archived** | BooleanField | default `False`. Set `True` when admin "deletes" or bulk-archives a record. Hides it from the admin's active list only — never affects the resident's own view |
| **requested_by** | ForeignKey → `User` | nullable, `on_delete=SET_NULL`, ties each request to the resident who created it |
| created_at / updated_at | DateTimeField | auto-managed |

**Roles (the two required logins):**

This app uses Django's built-in `User` model rather than inventing a separate `Role` table — simpler, and it's what `django.contrib.admin` already relies on:

- `is_staff = True` → **Admin** role → sees and manages every non-archived request; cannot create new ones.
- `is_staff = False` (default on signup) → **Resident/User** role → sees and manages only their own requests, archived or not (enforced via `get_queryset()` and `UserPassesTestMixin.test_func()` in `views.py`).

Admin accounts are created via `python manage.py createsuperuser`; resident accounts self-register via `/signup/`.

**Status lifecycle:**

```
Submitted for Collection → Pending Pickup → Collected → Completed
```
A new request always starts at `submitted` (set in `CollectionCreateView.form_valid()`, not chosen by the resident). Only an admin editing an *existing* record gets a `status` control in the form (added conditionally in `WasteCollectionForm.__init__`); residents never see or control it.

**Request flow (create):**

```
Resident fills form (waste type chosen via image card)
   → CollectionCreateView.form_valid()
   → form.instance.requested_by = request.user
   → form.instance.status = 'submitted'
   → save() → redirect to collection_list
```
`CollectionCreateView` also runs `UserPassesTestMixin.test_func() = not is_admin(user)`, so an admin hitting `/collection/new/` directly gets a 403 — the "+ New Collection" / "+ Schedule Collection" buttons are also hidden from admins in `base.html`, `home.html`, and `collection_list.html`.

**Delete / archive flow:**

```
Resident deletes own 'submitted' request  → real, permanent delete (nothing worth preserving pre-acceptance)
Admin deletes any request                 → archived = True, save() — row is kept, just hidden from admin's list
Admin bulk-archives a month               → WasteCollection.objects.filter(status='completed', collection_date__year=Y,
                                              collection_date__month=M, archived=False).update(archived=True)
```
Both paths live in `CollectionDeleteView` (overriding `post()`, not `delete()` — Django 4.0+ routes `DeleteView` POSTs through `form_valid()`/`post()` internally, so a `delete()` override is silently skipped on modern Django) and the standalone `ArchiveCompletedByMonthView`.

**Access control flow (view/edit/delete):**

```
LoginRequiredMixin  → must be logged in at all
UserPassesTestMixin → is_admin(user) OR object.requested_by == user
                       (delete additionally requires object.status == 'submitted' for residents)
```

**URL map:**

| URL | View | Purpose |
|---|---|---|
| `/` | HomeView | Public landing page; dashboard (own stats + recent requests) once logged in |
| `/signup/` | SignUpView | Create resident account |
| `/login/` | CollectionLoginView | Log in |
| `/logout/` | CollectionLogoutView | Log out |
| `/collections/` | CollectionListView | List (role-filtered, excludes archived for admins) |
| `/collection/new/` | CollectionCreateView | New request — residents only |
| `/collection/<pk>/` | CollectionDetailView | View one request |
| `/collection/<pk>/edit/` | CollectionUpdateView | Edit |
| `/collection/<pk>/delete/` | CollectionDeleteView | Delete (resident, submitted-only) / Archive (admin) |
| `/collections/archive-completed/` | ArchiveCompletedByMonthView | Admin-only: bulk-archive a month of completed requests |
| `/admin/` | Django admin | Staff-only bulk management |

---

## 3. Implementation Notes

- Two-role login is implemented via `is_staff` on Django's `User` model — no extra migration for a roles table was needed, keeping auth simple and reusing the battle-tested Django auth system.
- `requested_by` is a nullable `ForeignKey` (`on_delete=SET_NULL`) so deleting a user account doesn't cascade-delete their historical collection records.
- `archived` is a second, independent layer of "soft" record-keeping on top of that: it lets admins keep their working list clean (especially after bulk-archiving a month of completed jobs) without ever destroying a resident's own history — the two residents-facing views (`home.html` dashboard counts and `collection_list.html`) never filter on `archived`, only the admin's `CollectionListView.get_queryset()` does.
- All CRUD views are Django generic class-based views (`ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`) plus one plain `View` (`ArchiveCompletedByMonthView`), wrapped with `LoginRequiredMixin` and, where per-object ownership or role matters, `UserPassesTestMixin`.
- The waste-type field is a `forms.RadioSelect` widget under the hood, but rendered in `collection_form.html` as clickable image cards, kept visually in sync with the checked radio input via a small inline `<script>` block.
- App static assets (CSS + the six waste-type SVG icons) live inside the `recycling` app itself (`recycling/static/...`) rather than a project-level `static/` folder, so no `STATICFILES_DIRS` entry is required — Django's `AppDirectoriesFinder` picks them up automatically as long as `django.contrib.staticfiles` is installed.

**Running locally:**

```bash
pip install django
python manage.py migrate
python manage.py createsuperuser   # creates an admin account
python manage.py runserver
```

Visit `http://127.0.0.1:8000/signup/` to create a resident account, or log in with the superuser account created above to act as admin.

---

## 4. User Guide

### As a Resident (User)

1. Go to `/signup/` and create an account.
2. Log in at `/login/`.
3. On the home page, see a quick dashboard of your own requests by status.
4. Click **"+ New Collection"** to submit a pickup request — fill in household name, address, phone, pick a waste type from the image cards, weight, and preferred date.
5. On the **Collections** page you'll see only *your own* requests (including any an admin has since archived), along with their current status.
6. Click **View** to see full details, **Edit** to change a request, or **Delete** to cancel it — deletion is only available while a request is still `Submitted for Collection`; once staff accept it, it's locked.

### As Admin (Staff)

1. Log in with a superuser/staff account (created via `createsuperuser`).
2. The **Collections** page shows every resident's non-archived requests, with a "Requested By" column. There is no "+ New Collection" option — admins manage requests, they don't create them.
3. Click **Edit** on any record to move it forward through the status pipeline (`Submitted → Pending Pickup → Collected → Completed`).
4. Click **Delete** to archive a record out of your active list — the resident who requested it will still see it in their own history.
5. Use the **"Archive completed for month"** picker at the top of the Collections page to clear out an entire month of completed jobs in one action.
6. For bulk work — searching by household/address/phone, filtering by waste type or status, or browsing by date — use `/admin/`, which is pre-configured with search fields, filters, and a date hierarchy (see `admin.py`).

### Status Lifecycle

```
Submitted for Collection → Pending Pickup → Collected → Completed
```

---

## 5. Possible Future Enhancements

- Email notification to the resident when status changes.
- Map view of pending pickups for route planning.
- An "Archived" tab/filter on the admin's Collections page, so staff can review or (rarely) permanently purge old archived records instead of them being invisible-but-permanent.

