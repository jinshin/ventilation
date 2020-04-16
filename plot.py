import sched, time, datetime, pickle, random
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

dt_list = []
t_list = []
p_list = []
h_list = []
co2_list = []
fig = 0
ax = 0

def time_func():
  global dt_list, t_list, p_list, h_list, co2_list
  s.enter(300, 1, time_func, ())
  cdate=datetime.datetime.now()
  data="0,0,0,0"
  co2=800
  #Get TPH
  try:
    tphfile=open("/tmp/tph","r")
    data=tphfile.read()
    tphfile.close()
  except:
    print ("No TPH Data")
  cdate,t,p,h=map(float,data.split(","))

  cdate=datetime.datetime.fromtimestamp(cdate)
  #cdate=datetime.datetime.now()

  #print(cdate,t,p,h)
  #Get CO2
  #ToDo - add timestamp as well
  try:
    tphfile=open("/tmp/co2level","r")
    co2=tphfile.read()
    tphfile.close()
  except:
    print ("No CO2 Data")
  #print(co2)
  MAXLEN=288

#  for x in range(20):
#    t=19+random.random()

  dt_list.append(cdate); t_list.append(float(t));  p_list.append(float(p));  h_list.append(float(h));  co2_list.append(float(co2))
  if (len(dt_list)>MAXLEN): dt_list.pop(0)
  if (len(t_list)>MAXLEN): t_list.pop(0)
  if (len(p_list)>MAXLEN): p_list.pop(0)
  if (len(h_list)>MAXLEN): h_list.pop(0)
  if (len(co2_list)>MAXLEN): co2_list.pop(0)

  #st=datetime.datetime.now()
  #dump data
  try:
    pfile=open("/var/log/plot.pkl","wb+")
    pickle.dump(dt_list,pfile,-1)
    pickle.dump(t_list,pfile,-1)
    pickle.dump(p_list,pfile,-1)
    pickle.dump(h_list,pfile,-1)
    pickle.dump(co2_list,pfile,-1)
    pfile.close()
  except:
    print("Cannot pickle data")

  global fig, ax
  ax.plot(dt_list, t_list)
  ax.set(xlabel='', ylabel='Temperature, Celcius',
       title='Temperature: '+str(t)+'В°C' )
  ax.grid()
  ax.ticklabel_format(style='plain', useOffset=False, axis='y')
  fig.autofmt_xdate(rotation=45)
  ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
  fig.savefig("/var/www/t.png")
  plt.cla()

  ax.plot(dt_list, p_list)
  ax.set(xlabel='', ylabel='Pressure, hPa',
       title='Pressure: '+str(p)+' hPa')
  ax.grid()
  ax.ticklabel_format(style='plain', useOffset=False, axis='y')
  fig.autofmt_xdate(rotation=45)
  ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
  fig.savefig("/var/www/p.png")
  plt.cla()

  ax.plot(dt_list, h_list)
  ax.set(xlabel='', ylabel='Relative Humidity, %',
       title='Relative humidity: '+str(h)+'%')
  ax.grid()
  ax.ticklabel_format(style='plain', useOffset=False, axis='y')
  fig.autofmt_xdate(rotation=45)
  ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
  fig.savefig("/var/www/h.png")
  plt.cla()

  ax.plot(dt_list, co2_list)
  ax.set(xlabel='', ylabel='CO2, ppm',
       title='CO2: '+str(co2))
  ax.grid()
  ax.ticklabel_format(style='plain', useOffset=False, axis='y')
  ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
  fig.autofmt_xdate(rotation=45)
  fig.savefig("/var/www/co2.png")
  plt.cla()

  #print(datetime.datetime.now()-st)

  #print(dt_list, t_list)

#------------------
#Restore data
try:
  pfile=open("/var/log/plot.pkl","rb")
  dt_list=pickle.load(pfile)
  t_list=pickle.load(pfile)
  p_list=pickle.load(pfile)
  h_list=pickle.load(pfile)
  co2_list=pickle.load(pfile)
  pfile.close()
except:
  print("Cannot load pickled data")

plt.style.use('dark_background')
fig, ax = plt.subplots()
fig.autofmt_xdate(rotation=45)

s = sched.scheduler(time.time, time.sleep)
s.enter(1, 1, time_func, ())
s.run()

while True:
    time.sleep(1)