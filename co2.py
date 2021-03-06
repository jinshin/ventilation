import os,serial, sched, time, socket, datetime

VentoIP = '192.168.0.20'
VentoPort = 4000

logfile = "/var/log/co2"
novent  = "/tmp/VENTOFF"

#Min
CO2_Level = 400
Vent_Speed = 22
CO2_Prev = CO2_Level
Speed_Prev = Vent_Speed
Temp = 0
Power_On = 0
Do_Control = 0
RH = 50

Night_Limit = 120
Day_Max = 255
Day_Limit = 160

Night_Start = datetime.time(23,0,0)
Day_Start = datetime.time(9,0,0)

def is_night():
    global Night_Start
    global Day_Start
    Current_Time = datetime.datetime.now().time()
    if Night_Start <= Day_Start:
        return Night_Start <= Current_Time <= Day_Start
    else:
        return Night_Start <= Current_Time or Current_Time <= Day_Start


def get_co2():
    global Temp
#use /dev/ttyAMA0 in Raspberry Pi
    ser = serial.Serial('/dev/ttyS2', baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.5)
    try:
        result=ser.write(bytes([0xff,0x01,0x86,0x00,0x00,0x00,0x00,0x00,0x79]))
    except:
        return 0
    time.sleep(0.1)
    try:
        s=ser.read(9)
    except:
        return 0
    chk = (s[1]+s[2]+s[3]+s[4]+s[5]+s[6]+s[7])%256
    chk = (0xff - chk) + 1
    if chk != s[8]:
        #CRC invalid, return 0
        return 0
    if s[0] == 0xff and s[1] == 0x86:
        Temp = s[4]-40
        return s[2]*256 + s[3]

def set_speed(speed):
    global VentoIP
    global VentoPort
    Device = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    Device.settimeout(1)
    sendstr = bytes('mobile','cp1251')
    sendstr = sendstr + bytes([0x05]) + (speed.to_bytes(1, byteorder='big')) + bytes([0xD, 0xA])
    Device.sendto(sendstr, (VentoIP, VentoPort))
    Device.close()

def switch_power():
    global VentoIP
    global VentoPort
    Device = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    Device.settimeout(1)
    sendstr = bytes('mobile','cp1251')
    sendstr = sendstr + bytes([0x03, 0x01, 0xD, 0xA])
    Device.sendto(sendstr, (VentoIP, VentoPort))
    Device.close()

def get_speed():
    global VentoIP, VentoPort, Power_On, RH

    ReturnSpeed = 0

    Device = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    Device.settimeout(1)
    sendstr = bytes('mobile','cp1251')
    sendstr = sendstr + bytes([0x01, 0xD, 0xA])
    try:
        Device.sendto(sendstr, (VentoIP, VentoPort))
    except:
        return 0
    try:
        Received, addr = Device.recvfrom(256)
    except:
        return 0
    Device.close()
    if Received[0:6] == b'master':
        X = 6
        while X < len (Received):
            SW = Received[X]
            if SW == 3:
                X+=1
                Power_On = Received[X]
                #print('Power: ',Received[X])
            elif SW == 4:
                X+=1
                #print('Preset speed: ',Received[X])
                if Received[X] != 4:
                    ReturnSpeed = (22+(Received[X]-1)*((255-22)//2))
            elif SW == 5:
                X+=1
                #print('Manual speed: ',Received[X])
                ReturnSpeed = (Received[X])
            elif SW == 8:
                X+=1
                RH = (Received[X])
            X+=1
    return ReturnSpeed

def get_settings():
    global VentoIP, VentoPort, Do_Control
    Device = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    Device.settimeout(1)
    sendstr = bytes('mobile','cp1251')
    sendstr = sendstr + bytes([0x02, 0xD, 0xA])
    try:
        Device.sendto(sendstr, (VentoIP, VentoPort))
    except:
        return 0
    try:
        Received, addr = Device.recvfrom(256)
    except:
        return 0
    Device.close()
    if Received[0:6] == b'master':
        X = 6
        while X < len (Received):
            SW = Received[X]
            if SW == 31:
                X+=1
                Do_Control = Received[X]
            X+=1
    return 0


CO2_Prev = 0
Speed_Prev = 0

def change_speed(speed_val):
    global Speed_Prev, Vent_Speed, Night_Limit, Day_Limit, CO2_Level

    Speed_Limit = 255
    if (is_night()):
       Speed_Limit = Night_Limit
    else:
       Speed_Limit = Day_Limit
       if CO2_Level > 1300:
          Speed_Limit = Day_Max

    Speed_Prev = Vent_Speed
    Vent_Speed = Vent_Speed + speed_val
    #limit max speed in night
    if Vent_Speed > Speed_Limit:
       Vent_Speed = Speed_Limit
    elif Vent_Speed < 22:
       Vent_Speed = 22
    if Vent_Speed != Speed_Prev:
       set_speed(Vent_Speed)

def log_data():
    global Temp, CO2_Level, Vent_Speed, CO2_Prev, Speed_Prev, Night_LImit, Day_Limit, logfile
    #write value to temp file to communicate with other scripts
    try:
      co2file=open("/tmp/co2level", "w+")
      co2file.write(str(CO2_Level))
      co2file.close()
    except:
      print("Ahem.")
    #write to log
    log_file = open(logfile, "a")
    log_file.write(time.strftime("%Y-%m-%d %H:%M")+" "+str(CO2_Level)+" "+str(Temp)+" "+str(RH)+" "+str(Vent_Speed)+" "+str (Power_On)+"\n")
    log_file.close()


def time_func():
    global Temp, CO2_Level, Vent_Speed, CO2_Prev, Speed_Prev, Night_LImit, Day_Limit, logfile
    s.enter(60, 1, time_func, ())
    CO2_Level = get_co2()
    if CO2_Level == 0:
        return
    Vent_Speed = get_speed()
    if Vent_Speed == 0:
        return

    if (os.path.isfile(novent)):
      if Power_On == 1:
        switch_power()
      log_data()
      return

    get_settings()
    #print (CO2_Level, Temp, Vent_Speed, Do_Control)
    if Do_Control == 1:
      change_speed(0)
      if CO2_Level > 950 and CO2_Prev < CO2_Level:
        change_speed(12)
      #elif CO2_Level < 800 and CO2_Prev >= CO2_Level:
      elif CO2_Level < 800:
        change_speed(-12)
      if CO2_Level <= 650 and Vent_Speed == 22 and Power_On == 1 and not is_night():
        switch_power()
      if CO2_Level > 750 and Power_On == 0:
        switch_power()
    CO2_Prev = CO2_Level

    log_data()

CO2_Prev = get_co2()
Speed_Prev = get_speed()
print("Starting:",CO2_Prev,Speed_Prev)

s = sched.scheduler(time.time, time.sleep)
s.enter(1, 1, time_func, ())
s.run()

while True:
    time.sleep(1)
