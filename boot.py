from imu import MPU6050                # importere MPU6050 klassen fra imu.py i lib mappen. (imu.py er fra E2023_MPU6050_micropython_ESP32-main avanceret. som vi har anvendt i undervisningen)  """   
from time import sleep                 # importering af sleep fra time modulet så vi kan pause koden med sleep() """
from machine import I2C, Pin, UART, ADC, PWM     # import af I2C, Pin, UART, ADC og PWM så vi kan bruge I2C og Pins fra esp32 """
from neopixel import NeoPixel          # import af neopixel

import umqtt_robust2 as mqtt
from gps_bare_minimum import GPS_Minimum

import _thread

###### Variabler ######


tackle_state = False
tackle_count = 0
tackle_tens = 10

pin_adc_bat = 34
bat_scaling = 4.2 / 850

# RGB
RED = 0
GREEN = 1


###### Config ######



#neopixel config
pix_amount = 12                              # variabel som definerer antallet af pixels
neo_pin = 26                                 # variabel som bruges til at definer hvilken pin som bruges til neopixel
neo_pin_speed = 25


#gps config
gps_port = 2                                 # ESP32 UART port, Educaboard ESP32 default UART port
gps_speed = 9600

#batteri config
pin_adc_bat = 35
bat_scaling = 4.2 / 850

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

def set_color(r, g, b):             # set_color functionen fra øvelse 3.2 i programmering omkring neopixel
    for i in range(pix_amount):
        neo_obj[i] = (r, g, b)
        neo_obj.write()

def read_battery_voltage_avg64():
    adc_val = 0
    for i in range(512):
        adc_val += bat_adc.read()      
    voltage = bat_scaling * (adc_val >> 9)
    print("Voltage: ",voltage)
    
    min_uvolt = 2762
    max_uvolt = 4200
    volt_procent = voltage * 1000
    percentage_of_battery = int((volt_procent-min_uvolt)/(max_uvolt-min_uvolt) * 100)
    print(percentage_of_battery, "%")
    if percentage_of_battery < 10:
        for i in range (5):
            set_color(int(255/4), 0, 0)
            sleep(1)
            set_color(0, 0, int(255/4))
            sleep(1)
            set_color(0,0,0)
        
        exit()
        
def get_adafruit_gps():
    speed = lat = lon = None # Opretter variabler med None som værdi
    if gps.receive_nmea_data():
        """ hvis der er kommet end bruggbar værdi på alle der skal anvendes """
        if gps.get_speed() != -999 and gps.get_latitude() != -999.0 and gps.get_longitude() != -999.0 and gps.get_validity() == "A":
            """ gemmer returværdier fra metodekald i variabler """
            speed =str(gps.get_speed())
            lat = str(gps.get_latitude())
            lon = str(gps.get_longitude())
            """ returnerer data med adafruit gps format """
            return speed + "," + lat + "," + lon + "," + "0.0"
        else: # hvis ikke både hastighed, latitude og longtitude er korrekte 
            print(f"GPS data to adafruit not valid:\nspeed: {speed}\nlatitude: {lat}\nlongtitude: {lon}")
            return False
    else:
        return False       


#### program ###
print("tænder op")

read_battery_voltage_avg64()

print("running startup")

get_adafruit_gps()

acceleration = imu.accel
print("imu pos: ", acceleration.y)

while(mqtt.besked != "rdy"):
    sleep(1)
    
    if len(mqtt.besked) != 0: # Her nulstilles indkommende beskeder
        mqtt.besked = ""            
    mqtt.sync_with_adafruitIO() # igangsæt at sende og modtage data med Adafruit IO             
    print(".", end = '') # printer et punktum til shell, uden et enter

# kommando = 1
# 
# while(kommando != "rdy"):
#     sleep(0.1)
#     kommando = input("type 'rdy' when ready: ").lower()
# 
# 
# 
# 
# 
# 