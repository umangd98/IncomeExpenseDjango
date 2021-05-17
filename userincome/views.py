from django.shortcuts import render, redirect
from .models import Source, UserIncome
from userpreferences.models import UserPreference
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
import json
from django.http import JsonResponse

# Create your views here.


def search_income(request):
  if request.method == 'POST':
    search_str = json.loads(request.body).get('searchText')
    incomes = UserIncome.objects.filter(amount__istartswith=search_str, owner=request.user) | UserIncome.objects.filter(date__startswith=search_str, owner=request.user) | UserIncome.objects.filter(description__icontains=search_str, owner=request.user) | UserIncome.objects.filter(source__icontains=search_str, owner=request.user)
    # print(expenses)
    data = incomes.values()
    # print(data)
    return JsonResponse(list(data), safe=False)


@login_required(login_url='/authentication/login')
def index(request):
  sources = Source.objects.all()
  incomes = UserIncome.objects.filter(owner=request.user)
  paginator = Paginator(incomes,5)
  page_number = request.GET.get('page')
  page_obj = Paginator.get_page(paginator,page_number)
  currency = UserPreference.objects.get(user=request.user).currency
  context = {
    'incomes': incomes,
    'page_obj':page_obj,
    'currency':currency
  }
  return render(request, 'income/index.html', context)

def add_income(request):
  sources = Source.objects.all()
  context = {
    'sources': sources, 
    'values': request.POST
  }
  if request.method=='GET':
    return render(request, 'income/add_income.html', context)

  if request.method == 'POST':
    amount = request.POST['amount']
    if not amount:
      messages.error(request, 'No amount provided.')
      return render(request, 'income/add_income.html', context)
    description = request.POST['description']
    if not description:
      messages.error(request, 'No description provided.')
      return render(request, 'income/add_income.html', context)
    date = request.POST['date']
    if not date:
      messages.error(request, 'No date provided.')
      return render(request, 'income/add_income.html', context)
    source = request.POST['source']
    UserIncome.objects.create(amount=amount, date=date, source = source , description=description, owner = request.user)
    messages.success(request, 'Income Saved Successfully.')
    return redirect('incomes')
    
def income_edit(request, id):
  income = UserIncome.objects.get(id=id)
  sources = Source.objects.all()
  if request.method=='GET':
    context = {
      'income': income, 
      'values': income,
      'sources': sources, 
    }
    return render(request, 'income/edit-income.html', context)
  elif request.method=='POST':
    amount = request.POST['amount']
    if not amount:
      messages.error(request, 'No amount provided.')
      return render(request, 'income/edit-income.html', context)
    description = request.POST['description']
    if not description:
      messages.error(request, 'No description provided.')
      return render(request, 'income/edit-income.html', context)
    date = request.POST['date']
    if not date:
      messages.error(request, 'No date provided.')
      return render(request, 'income/edit-income.html', context)
    source = request.POST['source']
    # income.objects.create(amount=amount, date=date, category = category , description=description, owner = request.user)
    income.amount = amount
    income.date = date
    income.description = description
    income.source = source
    income.save()
    messages.success(request, 'Income Updated Successfully.')
    return redirect('incomes')


def delete_income(request, id):
  income = UserIncome.objects.get(id=id)
  if income:
    income.delete()
  messages.success(request, 'Income removed.')
  return redirect('incomes')