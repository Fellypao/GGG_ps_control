#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 14:17:22 2025

@author: Fellype do Nascimento
This is a basic control program for the GREMI power supply
version: 20250220
"""
version = "20250220"
import serial # this requires pyserial to be installed
import sys
import os
from time import sleep
import tkinter as tk
from tkinter import messagebox

COMPORT_TIMEOUT = 1         # in seconds
COMPORT_SPEED = 2400        # in baud
min2sec = 60                # to convert minutes to seconds

# try to automatically detect the port in which the power supply is connected
def findCOMport():
  if sys.platform != 'linux':
    port_range = range(1, 9)  # COM1 to COM8
    port_prefix = 'COM'
  else:
    port_range = range(0, 8)  # /dev/ttyUSB0 to /dev/ttyUSB7
    port_prefix = '/dev/ttyUSB'

  for pn in port_range:
    COMPORT = port_prefix + str(pn)
    if os.path.exists(COMPORT):
      try:
        ser = serial.Serial(COMPORT, COMPORT_SPEED, timeout=COMPORT_TIMEOUT)
        ser.close()  # Close the port after testing
        return COMPORT
      except Exception:
        continue  # Continue searching if the port cannot be opened

  # If no port is found, show an error message and return None
  messagebox.showerror("Error!", "Device not found! Check if it is connected properly.")
  return None
    
# function for reading the values of operation parameters
def read_values():
  try:
    frequency = float(entry_frequency.get().replace(',','.'))
    time_off = int(entry_time_off.get().replace(',','.'))
    treatment_duration = int(float(entry_treatment_duration.get().replace(',','.'))*min2sec)
    number_of_pulses = int(entry_number_of_pulses.get().replace(',','.'))
    
    # Validate input values
    if frequency <= 0 or time_off <= 0 or treatment_duration <= 0 or number_of_pulses <= 0:
      raise ValueError("Values must be positive and non-zero.")
    if frequency > 20000:
      raise ValueError("Frequency is out of range. Please, insert a value >0 and <= 20000.")
    
    return frequency, time_off, treatment_duration, number_of_pulses
  except ValueError as e:
    messagebox.showerror("Error!", f"Invalid input: {e}")
    return None, None, None, None

# Function for starting the plasma treatment (plasma source on)
def start():
  if ser is None:
    messagebox.showerror("Error!", "Serial port is not connected.")
    return

  frequency, time_off, treatment_duration, number_of_pulses = read_values()
  if frequency is None or time_off is None or treatment_duration is None or number_of_pulses is None:
    return  # Error message already shown by read_values()

  # Disable the Start button after it is pressed
  button_start.config(state=tk.DISABLED)
  # Enable the Stop button
  button_stop.config(state=tk.NORMAL)

  try:
    commands = [
      (b'T\n', str(time_off).zfill(3)),
      (b'N\n', str(number_of_pulses).zfill(3)),
      (b'M\n', str(treatment_duration)),
      (b'F\n', str(frequency)),
      (b'D\r\n', '')  # No additional data for this command
      ]

    for cmd, data in commands:
      ser.write(cmd)
      sleep(0.25)
      if data:
        ser.write(data.encode() + b'\n')
        sleep(0.25)

  except Exception as e:
    messagebox.showerror("Error!", f"{e}")
  
# Function for stoping the plasma treatment (plasma source off)
def stop():
  if ser is None:
    messagebox.showerror("Error!", "Serial port is not connected.")
    return

  try:
    # ser.write(b'A\n')
    ser.write(b'D\n')
    # Disable the Stop button
    button_stop.config(state=tk.DISABLED)
    # Enable the Start button
    button_start.config(state=tk.NORMAL)
  except Exception as e:
    messagebox.showerror("Error!", f"{e}")

# Exit the program
def Exit():
  if ser is not None:
    ser.close()
  root.destroy()

# Update info
def Update():
  frequency, time_off, treatment_duration, number_of_pulses = read_values()
  if frequency is None or time_off is None or treatment_duration is None or number_of_pulses is None:
    return  # Error message already shown by read_values()
  pulse_period = 1e3/frequency
  burst_perriod = number_of_pulses*pulse_period + time_off
  burst_perriod_result.config(state=tk.NORMAL)
  burst_perriod_result.delete(0, tk.END)
  burst_perriod_result.insert(0, f"{burst_perriod:.3f}")
  burst_perriod_result.config(state=tk.DISABLED)
  
  burst_frequency = 1e3/burst_perriod
  burst_frequency_result.config(state=tk.NORMAL)
  burst_frequency_result.delete(0, tk.END)
  burst_frequency_result.insert(0, f"{burst_frequency:.3f}")
  burst_frequency_result.config(state=tk.DISABLED)
  
  duty_cycle = 100*(burst_perriod - time_off)/burst_perriod
  duty_cycle_result.config(state=tk.NORMAL)
  duty_cycle_result.delete(0, tk.END)
  duty_cycle_result.insert(0, f"{duty_cycle:.2f}")
  duty_cycle_result.config(state=tk.DISABLED)

# Creating the main window
root = tk.Tk()
root.title("Power supply control (v. {})".format(version))

# Default values
std_frequency = 10000              # 10 kHz
std_time_off = 10                  # 10 miliseconds
std_treat_duration = 5             # 5 minutes
std_number_of_pulses = 10          # 10 pulses

try:
  port = findCOMport()
  ser = serial.Serial(port, COMPORT_SPEED, timeout=COMPORT_TIMEOUT)
except Exception:
  ser = None

if ser != None:
  # Creating the widgets
  label_frequency = tk.Label(root, text="Pulse frequency (Hz)\n(this must be > 0)")
  label_frequency.grid(row=0, column=0, padx=10, pady=10)
  
  entry_frequency = tk.Entry(root)
  entry_frequency.insert(0, str(std_frequency))  # Fill with default value
  entry_frequency.grid(row=0, column=1, padx=10, pady=10)
  
  label_time_off = tk.Label(root, text="Time off (ms)\n(time interval w/o voltage)")
  label_time_off.grid(row=1, column=0, padx=10, pady=10)
  
  entry_time_off = tk.Entry(root)
  entry_time_off.insert(0, str(std_time_off))  # Fill with default value
  entry_time_off.grid(row=1, column=1, padx=10, pady=10)
  
  label_treatment_duration = tk.Label(root, text="Treatment duration (minutes):")
  label_treatment_duration.grid(row=2, column=0, padx=10, pady=10)
  
  entry_treatment_duration = tk.Entry(root)
  entry_treatment_duration.insert(0, str(std_treat_duration))  # Fill with default value
  entry_treatment_duration.grid(row=2, column=1, padx=10, pady=10)
  
  label_number_of_pulses = tk.Label(root, text="Number of pulses\n(integer number, min=1)")
  label_number_of_pulses.grid(row=3, column=0, padx=10, pady=10)
  
  entry_number_of_pulses = tk.Entry(root)
  entry_number_of_pulses.insert(0, str(std_number_of_pulses))  # Fill with default value
  entry_number_of_pulses.grid(row=3, column=1, padx=10, pady=10)
  
  # Output fields
  burst_perriod_label = tk.Label(root, text="Burst period (ms):")
  burst_perriod_label.grid(row=4, column=0, padx=5, pady=5)
  burst_perriod_result = tk.Entry(root, state=tk.DISABLED)
  burst_perriod_result.grid(row=4, column=1, padx=5, pady=5)
  
  burst_frequency_label = tk.Label(root, text="Burst frequency (Hz):")
  burst_frequency_label.grid(row=5, column=0, padx=5, pady=5)
  burst_frequency_result = tk.Entry(root, state=tk.DISABLED)
  burst_frequency_result.grid(row=5, column=1, padx=5, pady=5)
  
  duty_cycle_label = tk.Label(root, text="Duty cycle (%):")
  duty_cycle_label.grid(row=6, column=0, padx=5, pady=5)
  duty_cycle_result = tk.Entry(root, state=tk.DISABLED)
  duty_cycle_result.grid(row=6, column=1, padx=5, pady=5)
  
  button_update = tk.Button(root, text="Update\nvalues", command=Update)
  button_update.grid(row=5, column=2, padx=10, pady=10)
  
  button_start = tk.Button(root, text="Start", command=start)
  button_start.grid(row=7, column=0, padx=10, pady=10)
  
  button_stop = tk.Button(root, text="Stop", command=stop)#, state=tk.DISABLED)
  button_stop.grid(row=7, column=1, padx=10, pady=10)
  
  button_exit = tk.Button(root, text="Exit", command=Exit)
  button_exit.grid(row=7, column=2, padx=10, pady=10)
  
  # Inicia o loop principal da interface gráfica
  root.mainloop()

else:
  messagebox.showerror("Error!", "Device not found! Check if it is connected properly.")
  Exit()
  # root.mainloop()
  
