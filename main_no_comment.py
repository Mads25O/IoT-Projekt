###### import ######
from imu import MPU6050                   
from time import sleep                 
from machine import ADC, I2C, Pin, UART, PWM     
from neopixel import NeoPixel         
import sys
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
pix_amount = 12                              
neo_pin = 33                                 
neo_pin_speed = 22


#gps config
gps_port = 2                                
gps_speed = 9600

#batteri config
pin_adc_bat = 34
bat_scaling = 3.88 / 1100

# Declare pins
pwm_pins = [32,4]
# Setup pins for PWM
pwms = [PWM(Pin(pwm_pins[RED])),PWM(Pin(pwm_pins[GREEN]))]
# Set pwm frequency
[pwm.freq(1000) for pwm in pwms]



####### objekter #######
uart = UART(gps_port, gps_speed)             
gps = GPS_Minimum(uart)                      


neo_obj = NeoPixel(Pin(neo_pin, Pin.OUT), pix_amount)
neo_obj_speed = NeoPixel(Pin(neo_pin_speed, Pin.OUT), pix_amount)

i2c = I2C(0)
imu = MPU6050(i2c)

#batteri
bat_adc = ADC(Pin(pin_adc_bat))
bat_adc.atten(ADC.ATTN_11DB)



###### Funktioner ######
def set_color(r, g, b):             
    for i in range(pix_amount):
        neo_obj[i] = (r, g, b)
        neo_obj.write()

#""" funktion til at aflæse batteri spænding
def read_battery_voltage():
    adc_val = bat_adc.read()
    voltage = bat_scaling * adc_val / 4095 * 3.3
    print("ADC Value: ",adc_val)
    return voltage

#""" funktion til at beregne den gennemsnitlige spænding over 512 målinger
def read_battery_voltage_avg64():
    adc_val = 0
    for i in range(512):
        adc_val += bat_adc.read()      
    voltage = bat_scaling * (adc_val >> 9)
    print(adc_val >> 9)
    print(voltage)
    min_uvolt = 3000
    max_uvolt = 4200
    volt_procent = voltage * 1000
    global percentage_of_battery
    percentage_of_battery = int(((volt_procent-min_uvolt)/(max_uvolt-min_uvolt) * 100))
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
    if percentage_of_battery < 10:
        for i in range (5):
            set_color(int(255/4), 0, 0)
            sleep(1)
            set_color(0, 0, int(255/4))
            sleep(1)
            set_color(0,0,0)
        
        sys.exit()
    return voltage



#""" funktion til hurtigt at printe akse positionerne
def akse_pos():                      
    acceleration = imu.accel
    print("y:", acceleration.y)
    print("x:", acceleration.x)
    print("z:", acceleration.z)
    sleep(1)

#""" funktionen for at at convertere gps data 
def get_adafruit_gps():
    speed = lat = lon = None 
    if gps.receive_nmea_data():
        
        if gps.get_speed() != -999 and gps.get_latitude() != -999.0 and gps.get_longitude() != -999.0 and gps.get_validity() == "A":
            
            speed =str(gps.get_speed())
            lat = str(gps.get_latitude())
            lon = str(gps.get_longitude())
            
            return speed + "," + lat + "," + lon + "," + "0.0"
        else:  
            print(f"GPS data to adafruit not valid:\nspeed: {speed}\nlatitude: {lat}\nlongtitude: {lon}")
            return False
    else:
        return False

#"""funktion der kører en animation på neopixel  
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

#""" Thread til tacklinger så vi kan registrere tacklinger
def neopixel_thread(dummy):
    tackle_state = False
    tackle_count = 0
    tackle_tens = 10
    
    while True:
        acceleration = imu.accel        
    
#Tacklings registrering
        if abs(acceleration.y) < 0.25 and tackle_state == False:
            tackle_state = True                                 
            print("tackling fundet")                            
            
            tackle_count += 1                                   
            print(tackle_count)                                 
            sleep(2)
        
        if tackle_count < 10:
            neo_obj[0] = (5,5,0)
            neo_obj[tackle_count] = (5,5,5)
            neo_obj.write()
        elif tackle_count >= 10 :
            anim(5,0,0)
  
  
  # GPS HASTIGHED 
        if gps.get_speed() > 0:
            speed_led = int(gps.get_speed()/3.6)            
            
            for i in range (speed_led):
                neo_obj_speed[i] = (1*i, 21*i, 0)
                neo_obj_speed.write()
                
            sleep(1)
            neo_obj_speed[i] = (0,0,0)
            neo_obj_speed.write()
                
        else:
            pass
                
        if abs(acceleration.y) > 0.8 and tackle_state == True:
       
            tackle_state = False                                 
            print("tackling slut")                               
            sleep(2)                                             


def startup():
    read_battery_voltage()
    read_battery_voltage_avg64()
    
    print("tænder op")

    read_battery_voltage_avg64()

    print("running startup")

    get_adafruit_gps()

    acceleration = imu.accel
    akse_pos()
    print("boot mqtt.besked", mqtt.besked)
    mqtt.web_print("type 'rdy' when ready")
    while(mqtt.besked != "rdy"):
        sleep(1)
        print("boot mqtt.besked", mqtt.besked)
        if len(mqtt.besked) != 0: 
            mqtt.besked = ""            
        mqtt.sync_with_adafruitIO()              
        print(".", end = '') 
        
    


###### Programmer ######
startup()
_thread.start_new_thread(neopixel_thread, (1,))        
while True:    
    read_battery_voltage_avg64()
    
    try:
        
        gps_data = get_adafruit_gps()
        
        if gps_data: 
            print(f'\ngps_data er: {gps_data}')
            mqtt.web_print(gps_data, 'GhostriderDK/feeds/mapfeed/csv')
            sleep(4)
               
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
            sys.exit()
     
        if len(mqtt.besked) != 0: 
            mqtt.besked = ""            
        mqtt.sync_with_adafruitIO()              
        print(".", end = '')         
    
    except KeyboardInterrupt:
        print('Ctrl-C pressed...exiting')
        mqtt.c.disconnect()
        mqtt.sys.exit()

