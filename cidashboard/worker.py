from cidashboard.models import CISystem, CIStatus


for ci_system in CISystem.objects.all():
    ci_system.update_all()

    current = ci_system.statuses.last()
    latest = CIStatus.make_from_results(
        ci_system=ci_system,
        results=ci_system.latest_rule_results(change_ci_status=True)
    )
    print repr(latest)

    if current != latest:
        latest.save()
