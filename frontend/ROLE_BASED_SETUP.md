# Eventify role-based frontend

## Included UI
- Register as Student, Faculty Advisor, or HOD.
- Login as Student, Faculty Advisor, or HOD.
- Login checks the authenticated user's role returned by `/api/auth/me/` and refuses mismatched role selections.
- Dashboard hides Approvals for Students and shows it for Faculty Advisors/HODs.
- Existing Create Event and dashboard pages/API service are retained.

## Backend contract required
The frontend sends `role` (`STUDENT`, `FACULTY_ADVISOR`, or `HOD`) and `club` in `/api/auth/register/`. The Django registration serializer/view must accept and validate these fields. Do not trust the frontend for authorization: enforce all role and club constraints in Django.

Preserve the established backend rules:
- At most one active Faculty Advisor and one active HOD per club.
- A person can hold the relevant role in only one club.
- Deactivation retains the old inactive account; a replacement can be assigned.
- Pending approvals transfer to the replacement approver without changing event status.
- Venue create/deactivate is Django Admin/superuser only.
- Faculty Advisor/HOD can only access approvals assigned to their club/role; Students cannot approve events.

If staff self-registration is not permitted by the Django policy, the backend should reject it with a clear validation message and use its authorized invitation/admin flow. A role dropdown is not a security boundary.

## Run
```powershell
npm install
npm run dev
```

Build check:
```powershell
npm run build
```
