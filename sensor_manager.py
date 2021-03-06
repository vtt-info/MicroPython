# filename: sensor_manager.py
# WEMOS D1 Mini Board GPIO Map: D8 pull_down, D4 pull_down
# D0=16, D1=5, D2=4, D3=0, D4=2, D5=14, D6=12, D7=13, D8=15
import machine, time

class Sensor_DHT22():
  def __init__(self, pin):
    if not isinstance(pin, int):
      raise TypeError('pin must be integer')
    
    from dht import DHT22
    self.sensor = DHT22(machine.Pin(pin))
    time.sleep( 1 ) # some delay to stabilize sensor
    self.t = None
    self.h = None
  def read(self):
    self.sensor.measure()
    self.t, self.h = self.sensor.temperature(), self.sensor.humidity()
    self.t, self.h = round(self.t,1), round(self.h,1)
    return [self.t, self.h]
  @property
  def values(self):
    return [self.t, self.h]
  @property
  def values_dict(self):
    return {'t': self.t, 'h': self.h}
#End of Sensor_DHT22

class Sensor_DHT11():
  def __init__(self, pin):
    if not isinstance(pin, int):
      raise TypeError('pin must be integer')
      
    from dht import DHT11
    self.sensor = DHT11(machine.Pin(pin))
    time.sleep(1) # some delay to stabilize sensor
    self.t = None
    self.h = None
  def read(self):
    self.sensor.measure()
    self.t, self.h = self.sensor.temperature(), self.sensor.humidity()
    self.t, self.h = round(self.t,1), round(self.h,1)
    return [self.t, self.h]
  @property
  def values(self):
    return [self.t, self.h]
  @property
  def values_dict(self):
    return {'t': self.t, 'h': self.h}
#End of Sensor_DHT11

class Sensor_BME280():
  def __init__(self, i2c, address=0x76):
    if not isinstance(i2c, machine.I2C):
      raise TypeError('I2C object required.')
      
    from bme280 import BME280
    self.bme = BME280(i2c=i2c,address=address)
    self.t = None
    self.h = None
    self.p = None
  def read(self):
    self.t, self.p, self.h = self.bme.values
    self.t = round(self.t,1)
    self.p = round(self.p,2)
    self.h = round(self.h,1)
    return [self.t, self.h, self.p]
  @property
  def values(self):
    return [self.t, self.h, self.p]
  @property
  def values_dict(self):
    return {'t': self.t, 'h': self.h, 'p': self.p}
#End of Sensor_BME280

class Sensor_BH1750FVI():
  #adaptation from https://github.com/catdog2/mpy_bh1750fvi_esp8266
  def __init__(self, i2c, address=0x23):
    if not isinstance(i2c, machine.I2C):
      raise TypeError('I2C object required.')
    self.i2c = i2c
    self.address = address
    self.lux = None
  def read(self):
    self.i2c.writeto(self.address, b'\x00') # make sure device is in a clean state
    self.i2c.writeto(self.address, b'\x01') # power up
    self.i2c.writeto(self.address, bytes([0x23])) # set measurement mode
    time.sleep_ms(180)
    raw = self.i2c.readfrom(self.address, 2)
    self.i2c.writeto(self.address, b'\x00') # power down again
    # we must divide the end result by 1.2 to get the lux
    self.lux = ((raw[0] << 24) | (raw[1] << 16)) // 78642
    return self.lux
  @property
  def values(self):
    return [self.lux]
  @property
  def values_dict(self):
    return {'lux': self.lux}
#End of Sensor_BH1750FVI

class Sensor_DS18B20():
  def __init__(self, pin):
    if not isinstance(pin, int):
      raise TypeError('pin must be integer')
    
    from onewire import OneWire
    from ds18x20 import DS18X20
    ow = OneWire(machine.Pin(ds18b20_pin)) 
    ow.scan()
    ow.reset()
    self.ds18b20 = DS18X20(ow)
    self.roms = self.ds18b20.scan()
    self.temps = [None for rom in self.roms]
  def read(self):
    self.ds18b20.convert_temp()
    time.sleep_ms(750)
    for i, rom in enumerate(self.roms):
      t = self.ds18b20.read_temp(rom)
      self.temps[i] = round(t, 1)
    return self.temps
  @property
  def values(self):
    return self.temps
  @property
  def values_dict(self):
    temps_dict = {}
    for i, value in enumerate(self.temps):
      temps_dict['t{}'.format(i)] = value
    return temps_dict
#End of Sensor_DS18B20

class Sensor_BUTTONS():
  def __init__(self, pins):
    if not isinstance(pins, list):
      raise TypeError('pins must be a list of pins')
    
    self.buttons = []
    for pin in pins:
      if not isinstance(pin, int):
        raise TypeError('pin must be a integer')
      self.buttons.append(machine.Pin(pin, machine.Pin.OUT))
    self.states = [button.value() for button in self.buttons]
    self.previews_states = [value for value in self.states]
    self.new_event = False
  def read(self):
    self.new_event = False
    for i, button in enumerate(self.buttons):
      self.previews_states[i] = self.states[i]
      self.states[i] = button.value()
      self.new_event = self.new_event or (self.states[i] != self.previews_states[i])
    return self.states
  @property
  def values(self):
    return self.states
  @property
  def values_dict(self):
    buttons_dict = {}
    for i in range(len(self.states)):
      buttons_dict['b{}'.format(i)] = self.states[i]
      buttons_dict['_b{}'.format(i)] = self.previews_states[i]
    return buttons_dict
#End Sensor_BUTTONS


class HCSR04():
  def __init__(self, trigger, echo, echo_timeout_us=500000):
    if isinstance(trigger, int) and isinstance(echo, int):
      self.trigger = machine.Pin(trigger, mode=machine.Pin.OUT, pull=None)    
      self.echo = machine.Pin(echo, mode=machine.Pin.IN, pull=None)
    else:
      raise TypeError('trigger and echo must be integer')
    self.echo_timeout_us = echo_timeout_us
    self.trigger.value(0)
    self.pulse_time = None
  def _send_pulse_and_wait(self):
    self.trigger.value(0)
    time.sleep_us(5)
    self.trigger.value(1)
    time.sleep_us(10)
    self.trigger.value(0)
    try:
      pulse_time = machine.time_pulse_us(self.echo, 1, self.echo_timeout_us)
      return pulse_time
    except OSError as ex:
      if ex.args[0] == 110: # 110 = ETIMEDOUT
        raise OSError('Out of range')
      raise ex
  def read(self):
    self.pulse_time = self._send_pulse_and_wait()
    return self.pulse_time
  @property
  def distance_mm(self):
    if self.pulse_time:
      return self.pulse_time * 100 // 582
    else:
      return None
  @property
  def distance_cm(self):
    if self.pulse_time:
      return (self.pulse_time / 2) / 29.1
    else:
      return None
  @property
  def values(self):
    return [self.distance_cm]
  @property
  def values_dict(self):
    return {'d': self.distance_cm}
#End of HCSR04
  
if __name__ == '__main__':
  print('Sensor manager')

  
#End of file
