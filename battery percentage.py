from machine import Pin, ADC, PWM
from time import sleep
from neopixel import NeoPixel

# RGB
RED = 0
GREEN = 1
BLUE = 2

# Declare pins
pwm_pins = [32,33,25]
# Setup pins for PWM
pwms = [PWM(Pin(pwm_pins[RED])),PWM(Pin(pwm_pins[GREEN])),
                PWM(Pin(pwm_pins[BLUE]))]
# Set pwm frequency
[pwm.freq(1000) for pwm in pwms]

# n = 12
# p = 26
# np = NeoPixel(Pin(p, Pin.OUT), n)

adc = ADC(Pin(25), atten=0)
adc_calibration_offset = 100000

# def set_color(r, g, b):
#     for pixel in range(n):
#         np[pixel] = (r, g, b)
#         np.write()

def deinit_pwm_pins():
    pwms[RED].deinit()
    pwms[GREEN].deinit()
    pwms[BLUE].deinit()


while True:
    
    m1 = adc.read_uv()
    sleep(0.010)
    m2 = adc.read_uv()
    sleep(0.010)
    m3 = adc.read_uv()
    sleep(0.010)
    m4 = adc.read_uv()
    sleep(0.010)
    m5 = adc.read_uv()
    
    gennemsnit = ((m1+m2+m3+m4+m5) // 5)
    
    # R1/(R1+R2) = 5.5 kohm /(5.5 kohm /22 kohm) = 0.2
    battery_voltage_avg = gennemsnit * 5
    
    battery = battery_voltage_avg - adc_calibration_offset
    min_uvolt = 3000000
    max_uvolt = 4200000
    percentage_of_battery = int((battery-min_uvolt)/(max_uvolt-min_uvolt) * 100)
    current_uvolt = battery
    
    if percentage_of_battery >= 70:
        pwms[RED].duty_u16(0)
        pwms[GREEN].duty_u16(65535)
        pwms[BLUE].duty_u16(0)
        
    elif percentage_of_battery >= 40:
        pwms[RED].duty_u16(65535)
        pwms[GREEN].duty_u16(25000)
        pwms[BLUE].duty_u16(0)
        
    elif percentage_of_battery >= 10:
        pwms[RED].duty_u16(65535)
        pwms[GREEN].duty_u16(0)
        pwms[BLUE].duty_u16(0)
    
    print("Battery Voltage1:", battery_voltage_avg)
    print("Battery Voltage2:", battery)
    print("Percentage:", percentage_of_battery)
    sleep(1)