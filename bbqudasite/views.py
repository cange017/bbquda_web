from django.shortcuts import render, reverse, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
import pandas as pd
import os
from users.forms import RegistrationForm
from bbquda.forms import CSVForm, LogForm
from .models import CSVUpload, LogUpload
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse
import csv
from io import StringIO
from django.core.files.base import ContentFile
from django.core.files import File
from django.views.generic.edit import DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.forms import AuthenticationForm






# Create your views here.


def index(request):
    return redirect('login')

#function for removing outliers
def clean(csv_file):
    return

#useful for allowing files that have periods in the name before an extension
def getName(strArr):
    name = ''
    for i in range(0, len(strArr) - 2):
        name = name + i 
    return name

def formhtml(request):
    #user just landed for the first time so show them the upload html
    if request.method == "GET":
        return render(request, 'form.html')
    
    #in the html called the uploaded file 'file'
    csv_file = request.FILES['file']

    #if we need to get the name of the file for organization reasons
    csv_file_string = csv_file.name.split('.') #array of the title of the uploaded file
    csv_file_name = getName(csv_file_string)
    df = None #need to declare the dataframe varaible so i can load it in the if

    #need seperate statements because need to specify delimiter with log file
    if csv_file.name.endswith('.log'):
        df = pd.read_csv(csv_file, delimiter=';')
        filtered_list = df[['Latitude', 'Longitude', 'Total Water Column (m)',
            'Temperature (c)', 'pH', 'ODO mg/L', 'Salinity (ppt)',
            'Turbid+ NTU', 'BGA-PC cells/mL']]
        #print(filtered_list) #just a check
        latitude = filtered_list['Latitude']
        print(df)
        return HttpResponse(latitude[0])

    elif csv_file.name.endswith('.csv'):
        df = pd.read_csv(csv_file)
        filtered_list = df[['Latitude', 'Longitude', 'Total Water Column (m)',
            'Temperature (c)', 'pH', 'ODO mg/L', 'Salinity (ppt)',
            'Turbid+ NTU', 'BGA-PC cells/mL']]
        #print(filtered_list) #just a check
        latitude = filtered_list['Latitude']
        print(df)
        return HttpResponse(latitude[0])

    else:
        messages.error(request, 'Please provide a .log or .csv formatted file')

def register(request):
    if request.user.is_authenticated:
        return redirect('my_missions')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False) 
            profile.save()
            login(request, profile)
            next = request.POST.get('next', '/') #redirect to where user wanted to go

            return HttpResponseRedirect(next)           
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})

@login_required
def logoutView(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')

@login_required
def upload_csv(request):
    if request.user.is_authenticated:
        user = request.user
    
        if request.method =='POST':
            form = CSVForm(request.POST, request.FILES)
        
        
            if form.is_valid():
                csv = form.save(commit=False) 
                csv.user = request.user
                csv.save()
            
                return redirect('')
        else:
            form = CSVForm()

        return render(request, 'upload_csv.html', {'form': form, 'user':user}) 
    return render(request, 'login.html') 

@login_required
def upload_log(request):
    
    if request.user.is_authenticated:
        user = request.user
    
        if request.method =='POST':
            form = LogForm(request.POST, request.FILES)
        
        
            if form.is_valid():
                log = form.save(commit=False) 
                log.user = request.user
                log.save()
                new_path = log.name + '.csv'
                with open(log.file.path, encoding="ISO-8859-1") as f, open(new_path, 'w') as f2: 
                    writer = csv.writer(f2)
                   
                    i = 0
                    for line in f:
                        writer.writerow([i] + line.rstrip().split(';'))
                        i += 1
                        if i == 10000:
                            break
                    
                    new_csv = CSVUpload(user = request.user)
                    new_file = open(new_path)
                    new_csv.file = File(new_file)
                    new_csv.name = log.name
                    new_csv.save()
            
                return redirect('my_missions')
        else:
            form = LogForm()

        return render(request, 'upload_log.html', {'form': form, 'user':user}) 
    return render(request, 'login.html') 

@staff_member_required
def mission_admin(request):
    missions = CSVUpload.objects.all()
    return render(request, 'mission_admin.html', {'missions': missions} )

@login_required 
def my_missions(request):
    if request.user.is_authenticated:
        user = request.user
        missions = CSVUpload.objects.filter(user = user)
       
        return render(request, 'my_missions.html', { 'user': user,'missions': missions})
    return redirect('login')

def download(request, pk):
    mission = CSVUpload.objects.get(id=pk)
    filename = mission.file.path
    response = FileResponse(open(filename, 'rb'))
    return response


class MissionDelete(DeleteView):
    model = CSVUpload
    success_url = reverse_lazy('my_missions')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

@login_required
def logoutView(request):
    logout(request)
    return redirect('login')

def mission_stats(request, pk):
    mission = CSVUpload.objects.get(id=pk)
    path = mission.file.path
    df = pd.read_csv(path) 
    water_count = df['Total Water Column (m)'].count()
    water_mean = df['Total Water Column (m)'].mean()
    water_std = df['Total Water Column (m)'].std()
    water_min = df['Total Water Column (m)'].min()
    water_max = df['Total Water Column (m)'].max()
    water_25 = df['Total Water Column (m)'].quantile(0.25)
    water_50 = df['Total Water Column (m)'].quantile(0.50)
    water_75 = df['Total Water Column (m)'].quantile(0.75)

    temp_count = df['Temperature (c)'].count()
    temp_mean = df['Temperature (c)'].mean()
    temp_std = df['Temperature (c)'].std()
    temp_min = df['Temperature (c)'].min()
    temp_max = df['Temperature (c)'].max()
    temp_25 = df['Temperature (c)'].quantile(0.25)
    temp_50 = df['Temperature (c)'].quantile(0.50)
    temp_75 = df['Temperature (c)'].quantile(0.75)

    pH_count = df['pH'].count()
    pH_mean = df['pH'].mean()
    pH_std = df['pH'].std()
    pH_min = df['pH'].min()
    pH_max = df['pH'].max()
    pH_25 = df['pH'].quantile(0.25)
    pH_50 = df['pH'].quantile(0.50)
    pH_75 = df['pH'].quantile(0.75)

    ODO_count = df['ODO mg/L'].count()
    ODO_mean = df['ODO mg/L'].mean()
    ODO_std = df['ODO mg/L'].std()
    ODO_min = df['ODO mg/L'].min()
    ODO_max = df['ODO mg/L'].max()
    ODO_25 = df['ODO mg/L'].quantile(0.25)
    ODO_50 = df['ODO mg/L'].quantile(0.50)
    ODO_75 = df['ODO mg/L'].quantile(0.75)

    salinity_count = df['Salinity (ppt)'].count()
    salinity_mean = df['Salinity (ppt)'].mean()
    salinity_std = df['Salinity (ppt)'].std()
    salinity_min = df['Salinity (ppt)'].min()
    salinity_max = df['Salinity (ppt)'].max()
    salinity_25 = df['Salinity (ppt)'].quantile(0.25)
    salinity_50 = df['Salinity (ppt)'].quantile(0.50)
    salinity_75 = df['Salinity (ppt)'].quantile(0.75)

    turbid_count = df['Turbid+ NTU'].count()
    turbid_mean = df['Turbid+ NTU'].mean()
    turbid_std = df['Turbid+ NTU'].std()
    turbid_min = df['Turbid+ NTU'].min()
    turbid_max = df['Turbid+ NTU'].max()
    turbid_25 = df['Turbid+ NTU'].quantile(0.25)
    turbid_50 = df['Turbid+ NTU'].quantile(0.50)
    turbid_75 = df['Turbid+ NTU'].quantile(0.75)

    BGA_count = df['BGA-PC cells/mL'].count()
    BGA_mean = df['BGA-PC cells/mL'].mean()
    BGA_std = df['BGA-PC cells/mL'].std()
    BGA_min = df['BGA-PC cells/mL'].min()
    BGA_max = df['BGA-PC cells/mL'].max()
    BGA_25 = df['BGA-PC cells/mL'].quantile(0.25)
    BGA_50 = df['BGA-PC cells/mL'].quantile(0.50)
    BGA_75 = df['BGA-PC cells/mL'].quantile(0.75)

    return render(request, 'mission_stats.html', {'mission': mission, 'water_count': water_count, 'water_mean': water_mean, 'water_std':water_std,
    'water_min':water_min, 'water_max':water_max, 'water_25':water_25, 'water_50':water_50, 'water_75':water_75, 'temp_count':temp_count,
    'temp_mean':temp_mean, 'temp_std':temp_std, 'temp_min':temp_min, 'temp_max':temp_max, 'temp_25':temp_25, 'temp_50':temp_50, 'temp_75':temp_75,
    'pH_count':pH_count, 'pH_mean':pH_mean, 'pH_std':pH_std, 'pH_min':pH_min, 'pH_max':pH_max, 'pH_25':pH_25, 'pH_50':pH_50, 'pH_75':pH_75,
    'ODO_count':ODO_count, 'ODO_mean':ODO_mean, 'ODO_std':ODO_std, 'ODO_min':ODO_min, 'ODO_max':ODO_max, 'ODO_25':ODO_25, 'ODO_50':ODO_50, 'ODO_75':ODO_75,
    'salinity_count':salinity_count, 'salinity_mean':salinity_mean, 'salinity_std':salinity_mean, 'salinity_std':salinity_std, 'salinity_min':salinity_min,
    'salinity_max':salinity_max, 'salinity_25':salinity_25, 'salinity_50':salinity_50, 'salinity_75':salinity_75, 'turbid_count':turbid_count,
    'turbid_mean':turbid_mean, 'turbid_std':turbid_std, 'turbid_min':turbid_min, 'turbid_max':turbid_max, 'turbid_25':turbid_25, 'turbid_50':turbid_50, 'turbid_75':turbid_75,
    'BGA_count':BGA_count, 'BGA_mean':BGA_mean, 'BGA_std':BGA_std, 'BGA_min':BGA_min, 'BGA_max':BGA_max, 'BGA_25':BGA_25, 'BGA_50':BGA_50, 'BGA_75':BGA_75} )