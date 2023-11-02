###### import ######
from imu import MPU6050                # importere MPU6050 klassen fra imu.py i lib mappen. (imu.py er fra E2023_MPU6050_micropython_ESP32-main avanceret. som vi har anvendt i undervisningen)  """   
from time import sleep                 # importering af sleep fra time modulet så vi kan pause koden med sleep() """
from machine import ADC, I2C, Pin, UART, PWM     # import af I2C, Pin, UART, ADC og PWM så vi kan bruge I2C og Pins fra esp32 """
from neopixel import NeoPixel          # import af neopixel

import umqtt_robust2 as mqtt
from gps_bare_minimum import GPS_Minimum

import _thread





###### Variabler ######

tackle_state = False
tackle_count = 0
tackle_tens = 10

# RGB
RED = 0
GREEN = 1


###### Config ######
#neopixel config
pix_amount = 12                              # variabel som definerer antallet af pixels
neo_pin = 33                                 # variabel som bruges til at definer hvilken pin som bruges til neopixel
neo_pin_speed = 22


#gps config
gps_port = 2                                 # ESP32 UART port, Educaboard ESP32 default UART port
gps_speed = 9600

#batteri config
pin_adc_bat = 34
bat_scaling = 4.2 / 2

# Declare pins
pwm_pins = [32,33]
# Setup pins for PWM
pwms = [PWM(Pin(pwm_pins[RED])),PWM(Pin(pwm_pins[GREEN]))]
# Set pwm frequency
[pwm.freq(1000) for pwm in pwms]



####### objekter #######
uart = UART(gps_port, gps_speed)             # UART object til gps som gør brug af UART 2 med baudrate på 9600 defineret med gps_port og gps_speed
gps = GPS_Minimum(uart)                      # GPS object som gør brug af gps_minimum modulet som vi importerede og bruger uart defineret ovenfor


neo_obj = NeoPixel(Pin(neo_pin, Pin.OUT), pix_amount)
neo_obj_speed = NeoPixel(Pin(neo_pin_speed, Pin.OUT), pix_amount)

i2c = I2C(0)
imu = MPU6050(i2c)

#batteri
bat_adc = ADC(Pin(pin_adc_bat))
bat_adc.atten(ADC.ATTN_11DB)



###### Funktioner ######
def set_color(r, g, b):             # set_color functionen fra øvelse 3.2 i programmering omkring neopixel
    for i in range(pix_amount):
        neo_obj[i] = (r, g, b)
        neo_obj.write()

#""" funktion til at aflæse batteri spænding
def read_battery_voltage():
    adc_val = bat_adc.read()
    voltage = bat_scaling * adc_val / 4095 * 3.3
#     print("ADC Value: ",adc_val)
    return voltage

#""" funktion til at beregne den gennemsnitlige spænding over 512 målinger
def read_battery_voltage_avg64():
    adc_val = 0
    for i in range(512):
        adc_val += bat_adc.read()      
    voltage = bat_scaling * (adc_val >> 9)
    
    min_uvolt = 3200
    max_uvolt = 4050
    volt_procent = voltage * 1000
    global percentage_of_battery
    percentage_of_battery = int(((volt_procent-min_uvolt)/(max_uvolt-min_uvolt) * 100) / 10000)
    if percentage_of_battery > 100:
        percentage_of_battery = 100
        
    elif percentage_of_battery >= 70:
        pwms[RED].duty_u16(0)
        pwms[GREEN].duty_u16(65535)
        
        
    elif percentage_of_battery >= 40:
        pwms[RED].duty_u16(65535)
        pwms[GREEN].duty_u16(25000)
        
        
    elif percentage_of_battery >= 10:
        pwms[RED].duty_u16(65535)
        pwms[GREEN].duty_u16(0)
        
    elif percentage_of_battery < 0:
        percentage_of_battery = 0
        
        
    print("Procent: ",percentage_of_battery,"%")
    sleep(0.1)
    return voltage


#"""funktion til at tænde antalet af lys tilsvarende til antal tacklinger registeret"""
def tackle_light():
    if tackle_count <= 10:
        neo_obj[tackle_count] = (5,5,5)
        neo_obj.write()
    elif tackle_count % 10 > 0:
         neo_obj[0] = (5/2,0,0)
         neo_obj[tackle_count - 10] = (5,5,5)
         neo_obj.write()
         sleep(0.2)

#""" funktion til hurtigt at printe akse positionerne så vi kan tjekke værdierne ved at tilføje akse_pos() til vores program"""
def akse_pos():                      
    acceleration = imu.accel
    print("y:", acceleration.y)
    print("x:", acceleration.x)
    print("z:", acceleration.z)
    sleep(1)

#""" funktionen for at at convertere gps data til data som adafruit kan bruge (taget fra adafruit_gps_main.py fra E2023_GPS_micropython_ESP32-main)  """
def get_adafruit_gps():
    speed = lat = lon = None # Opretter variabler med None som værdi
    if gps.receive_nmea_data():
        """ hvis der er kommet end bruggbar værdi på alle der skal anvendes """
        if gps.get_speed() != -999 and gps.get_latitude() != -999.0 and gps.get_longitude() != -999.0 and gps.get_validity() == "A":
            """ gemmer returværdier fra metodekald i variabler """
            speed =str(gps.get_speed()/3.6)
            lat = str(gps.get_latitude())
            lon = str(gps.get_longitude())
            """ returnerer data med adafruit gps format """
            return speed + "," + lat + "," + lon + "," + "0.0"
        else: # hvis ikke både hastighed, latitude og longtitude er korrekte 
            print(f"GPS data to adafruit not valid:\nspeed: {speed}\nlatitude: {lat}\nlongtitude: {lon}")
            return False
    else:
        return False


#"""funktion der kører en animation på neopixel som køre op fra pix 0 og 11 til 5 og 6. derefter kører den ned igen"""   
def anim(r,g,b):
    px = 0
    for i in range(74):
        neo_obj[px] = (r, g, b)
        neo_obj[11 - px] = (r, g, b)
        neo_obj.write()
        sleep(0.1)
        neo_obj[px] = (0, 0, 0)
        neo_obj[11 - px] = (0, 0, 0)
        px += 1
        if px == 11:
            px = 0

#""" Thread til tacklinger så vi kan registrere tacklinger uden gps og adafruit beskeder stopper vores aflæsning af tacklinger """
def neopixel_thread(dummy):
    tackle_state = False
    tackle_count = 0
    tackle_tens = 10
    
    while True:
        acceleration = imu.accel        # definerer variablen acceleration til acceleration opfanget af imu'en  """
    
#"""hvis accelerationens absolute værdi (værdien med fjernet fortegn. Så hvis værdien var negativ er den nu positiv.) er mindre en 0.3 OG vores tackle_state fortæller vi ikke er tacklet. så skal blokken kører"""
        if abs(acceleration.y) < 0.3 and tackle_state == False:
       
            tackle_state = True                                 # ændre vores tackle_state til at vi er tacklet """
            print("tackling fundet")                            # printer i shell 'tackling fundet' så vi kan se at det er registreret """
            tackle_count += 1                                   # lægger 1 til vores tackle_count """
            print(tackle_count)                                 # printer tackle_count så vi kan se den har talt tacklingen """
            sleep(2)
   
        
        if tackle_count < 10:
            neo_obj[0] = (5,5,0)
            neo_obj[tackle_count] = (5,5,5)
            neo_obj.write()
        elif tackle_count >= 10 :
            anim(5,0,0)
  
  
  # GPS HASTIGHED 
        if gps.get_speed() > 0:
            speed = int(gps.get_speed()/3.6)
            
            
            for i in range (speed):
                neo_obj_speed[i] = (1*i, 21*i, 0)
                neo_obj_speed.write()
                
        else:
            pass
            
            
        
        
            
        
        
   
#""" hvis den accelerationens absolute værdie er større en 0.8 OG vi har været 'er' tacklet skal blokken kører """      
        if abs(acceleration.y) > 0.8 and tackle_state == True:
       
            tackle_state = False                                 # ændre vores tackle_state til at vi ikke er tacklet mere """
            print("tackling slut")                               # printer i shell 'tackling slut' så vi kan være sikre på at den slutter tacklingen når spilleren rejser sig op """
            sleep(2)                                             # venter 2 sekunder da 




###### Programmer ######
_thread.start_new_thread(neopixel_thread, (1,))        
while True:    
    read_battery_voltage_avg64()
   
   #""" program der tager data fra gps funktionen og sender til adafruit hvis der er signal """
    try:
        # Hvis funktionen returnere en string er den True ellers returnere den False
        gps_data = get_adafruit_gps()
        
        
        #""" hvis der er korrekt data så send til adafruit"""
        if gps_data: 
            print(f'\ngps_data er: {gps_data}')
            mqtt.web_print(gps_data, 'GhostriderDK/feeds/mapfeed/csv')
            sleep(4)
        
        
        #"""hvis gps data er forkerte/invalid så skriv i shell og vent 1 sekund"""
        else: 
            print("waiting for GPS Signal data - move to somewhere with access to sky")
            sleep(1)
            
        if percentage_of_battery: 
            print(f'\nBatteri er: {percentage_of_battery}')
            mqtt.web_print(percentage_of_battery, 'GhostriderDK/feeds/battery/csv')
            sleep(4)
            
            
        if mqtt.besked == "stop":
            mqtt.c.disconnect()
            mqtt.sys.exit()
            for i in range(5):
                set_color(100, 0, 0)
                sleep(0.5)
                set_color(100, 50, 0)
                sleep(1)
                set_color(0,0,0)
            exit()
     
         
         
     
        if len(mqtt.besked) != 0: # Her nulstilles indkommende beskeder
            mqtt.besked = ""            
        mqtt.sync_with_adafruitIO() # igangsæt at sende og modtage data med Adafruit IO             
        print(".", end = '') # printer et punktum til shell, uden et enter        
    # Stopper programmet når der trykkes Ctrl + c
    except KeyboardInterrupt:
        print('Ctrl-C pressed...exiting')
        mqtt.c.disconnect()
        mqtt.sys.exit()
