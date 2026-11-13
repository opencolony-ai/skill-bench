def stats(request):
    return {"users": request.app.count_users()}


def legacy_stats(request):
    return {"users": request.app.count_users(), "v": 1}
