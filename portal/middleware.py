from django.http import JsonResponse
class JsonErrorMiddleware:
 def __init__(self,get_response): self.get_response=get_response
 def __call__(self,request):
  try:return self.get_response(request)
  except Exception as e:
   if request.path.startswith('/api/'):return JsonResponse({'success':False,'message':f'Server error: {e}'},status=500)
   raise
