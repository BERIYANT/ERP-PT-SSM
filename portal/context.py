def current_user(request):
    u=request.user
    return {'current_user': {'id':u.id if u.is_authenticated else None,'username':u.username if u.is_authenticated else None,'nama':getattr(u,'nama',None),'role':getattr(u,'role',None),'avatar':getattr(u,'avatar',None),'email':getattr(u,'email',None),'phone':getattr(u,'phone',None),'jabatan':getattr(u,'jabatan',None)}}
