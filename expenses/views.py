from django.shortcuts import render, redirect
from .models import Category, Expense
from userpreferences.models import UserPreference
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
import json
from django.http import JsonResponse, HttpResponse
import datetime
import csv
import xlwt
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from django.db.models import Sum
# Create your views here.


def search_expenses(request):
  if request.method == 'POST':
    search_str = json.loads(request.body).get('searchText')
    expenses = Expense.objects.filter(amount__istartswith=search_str, owner=request.user) | Expense.objects.filter(date__startswith=search_str, owner=request.user) | Expense.objects.filter(description__icontains=search_str, owner=request.user) | Expense.objects.filter(category__icontains=search_str, owner=request.user)
    # print(expenses)
    data = expenses.values()
    # print(data)
    return JsonResponse(list(data), safe=False)
@login_required(login_url='/authentication/login')
def index(request):
  categories = Category.objects.all()
  expenses = Expense.objects.filter(owner=request.user)
  paginator = Paginator(expenses,5)
  page_number = request.GET.get('page')
  page_obj = Paginator.get_page(paginator,page_number)
  currency = UserPreference.objects.get(user=request.user).currency
  context = {
    'expenses': expenses,
    'page_obj':page_obj,
    'currency':currency
  }
  return render(request, 'expenses/index.html', context)

def add_expense(request):
  categories = Category.objects.all()
  context = {
    'categories': categories, 
    'values': request.POST
  }
  if request.method=='GET':
    return render(request, 'expenses/add_expense.html', context)

  if request.method == 'POST':
    amount = request.POST['amount']
    if not amount:
      messages.error(request, 'No amount provided.')
      return render(request, 'expenses/add_expense.html', context)
    description = request.POST['description']
    if not description:
      messages.error(request, 'No description provided.')
      return render(request, 'expenses/add_expense.html', context)
    date = request.POST['date']
    if not date:
      messages.error(request, 'No date provided.')
      return render(request, 'expenses/add_expense.html', context)
    category = request.POST['category']
    Expense.objects.create(amount=amount, date=date, category = category , description=description, owner = request.user)
    messages.success(request, 'Expense Saved Successfully.')
    return redirect('expenses')
    

def expense_edit(request, id):
  expense = Expense.objects.get(id=id)
  categories = Category.objects.all()
  if request.method=='GET':
    context = {
      'expense': expense, 
      'values': expense,
      'categories': categories, 
    }
    return render(request, 'expenses/edit-expense.html', context)
  elif request.method=='POST':
    amount = request.POST['amount']
    if not amount:
      messages.error(request, 'No amount provided.')
      return render(request, 'expenses/edit-expense.html', context)
    description = request.POST['description']
    if not description:
      messages.error(request, 'No description provided.')
      return render(request, 'expenses/edit-expense.html', context)
    date = request.POST['date']
    if not date:
      messages.error(request, 'No date provided.')
      return render(request, 'expenses/edit-expense.html', context)
    category = request.POST['category']
    # Expense.objects.create(amount=amount, date=date, category = category , description=description, owner = request.user)
    expense.amount = amount
    expense.date = date
    expense.description = description
    expense.category = category
    expense.save()
    messages.success(request, 'Expense Updated Successfully.')
    return redirect('expenses')


def delete_expense(request, id):
  expense = Expense.objects.get(id=id)
  if expense:
    expense.delete()
  messages.success(request, 'Expense removed.')
  return redirect('expenses')


def expense_category_summary(request):
  today_date = datetime.date.today()
  six_months_ago = today_date - datetime.timedelta(days=180)
  expenses = Expense.objects.filter(date__gte=six_months_ago, date__lte=today_date, owner=request.user)
  finalrep = {}


  def get_category(expense):
    return expense.category
  def get_expense_category_amount(category):
    amount = 0
    filtered_by_category = expenses.filter(category =category)
    for item in filtered_by_category:
      amount+=item.amount
    return amount
  
  category_list = list(set(map(get_category, expenses)))

  for x in expenses:
    for y in category_list:
      finalrep[y] = get_expense_category_amount(y)

  return JsonResponse({'expense_category_data':finalrep}, safe=False)
  

def stats_view(request):
  return render(request,'expenses/stats.html')

def export_csv(request):
  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename=Expenses' + str(datetime.datetime.now()) + '.csv'
  writer = csv.writer(response)
  writer.writerow(['Amount', 'Description', 'Category', 'Date'])

  expenses = Expense.objects.filter(owner = request.user)

  for expense in expenses:
    writer.writerow([expense.amount, expense.description, expense.category, expense.date])
  return response


def export_excel(request):
  response = HttpResponse(content_type='application/ms-excel')
  response['Content-Disposition'] = 'attachment; filename=Expenses' + str(datetime.datetime.now()) + '.xls'
  wb = xlwt.Workbook(encoding='utf-8')
  ws = wb.add_sheet('Expenses')
  row_num = 0
  font_style = xlwt.XFStyle()
  font_style.font.bold = True
  columns = ['Amount', 'Description', 'Category', 'Date']
  for col_num in range(len(columns)):
    ws.write(row_num, col_num, columns[col_num], font_style)
  
  font_style= xlwt.XFStyle()
  rows = Expense.objects.filter(owner=request.user).values_list('amount', 'description', 'category', 'date')
  
  for row in rows:
    row_num+=1
    for col_num in range(len(columns)):
      ws.write(row_num, col_num, str(row[col_num]), font_style)
  
  wb.save(response)
  return response

def export_pdf(request):
  response = HttpResponse(content_type='application/pdf')
  response['Content-Disposition'] = 'inline; attachment; filename=Expenses' + str(datetime.datetime.now()) + '.pdf'
  response['Content-Transfer-Encoding'] = 'binary'
  expenses = Expense.objects.filter(owner = request.user)
  sum_ = expenses.aggregate(Sum('amount'))
  html_string = render_to_string('expenses/pdf_output.html', {'expenses': expenses, 'total': sum_['amount__sum']})
  html = HTML(string=html_string,base_url=request.build_absolute_uri())
  result = html.write_pdf()

  with tempfile.NamedTemporaryFile(delete=True) as output:
    output.write(result)
    output.flush()

    output = open(output.name, 'rb')
    response.write(output.read())
  return response
