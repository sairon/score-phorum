from django.shortcuts import render


def private_view(request):
    pass


def room_view(request):
    return render(request, template_name="")


def room_list(request):
    return render(request, template_name="")


def delete_message(request):
    pass
