# Beer lambert law calculations for the absorption of light in the gas cell using the the data from the hitran data.

import pandas as pd
import sys 
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

# Voeg de hoofdmap van het project toe aan het pad (één niveau boven Math)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Physics.Physics import PhysicsUtils
from Measurement.CalculatingAlpha import CalculateAlpha

class UseBeerLambert:
    def __init__(self, file_name, concentration, temperature=296, pressure_atm=1.0):
        self.file_name = file_name 
        self.concentration = concentration
        
    def alpha_at_wavelength(self, wavelength):
        calc = CalculateAlpha(self.file_name, self.concentration)
        wavelengths, alpha = calc.calculate_alpha()
        
        # search for alpha at the given wavelength
        idx = np.argmin(np.abs(wavelengths - wavelength))
        return alpha[idx]
    
    def using_beer_lambert(self, initial_intensity, distance, wavelength):
        alpha = self.alpha_at_wavelength(wavelength)
        return PhysicsUtils.calculate_beer_lambert(initial_intensity, distance, alpha)
    
    def sweeping_wavelengths(self, initial_intensity, distance, wavelength_range):
        calc = CalculateAlpha(self.file_name)
        wavelengths, alpha = calc.calculate_alpha()
        
        intensities = []
        for wl in wavelength_range:
            idx = np.argmin(np.abs(wavelengths - wl))
            alpha_wl = alpha[idx]
            intensity = PhysicsUtils.calculate_beer_lambert(initial_intensity, distance, alpha_wl)
            intensities.append(intensity)
            
        plt.plot(wavelength_range, intensities)
        plt.xlabel('wavelength (nm)')
        plt.ylabel('intensity after absorption (arb. units)')
        plt.show()
           
            
    def simulate_wms_2f(self, initial_intensity, distance, wl_center, scan_width, concentration=0.10):
        # 1. Definieer de Tijds- en Modulatie parameters
        f_mod = 10000      # Modulatiefrequentie (bijv. 10 kHz)
        f_scan = 10        # Hoe vaak per seconde scannen we over de hele piek? (10 Hz)
        fs = 1000000       # Sample rate van je "digitale detector" (1 MHz)
        t = np.arange(0, 1/f_scan, 1/fs) # Tijd voor 1 volledige scan
        
        # 2. Creëer het golflengte-signaal van de laser (Ramp + Sine)
        # De langzame sweep
        wl_ramp = np.linspace(wl_center - scan_width/2, wl_center + scan_width/2, len(t))
        # De snelle modulatie (a is de modulatie diepte, dit is een cruciale parameter om te tunen!)
        modulation_amplitude = 0.005 # in nm (pas dit aan op basis van je line-width!)
        wl_modulated = wl_ramp + modulation_amplitude * np.cos(2 * np.pi * f_mod * t)
        
        # 3. Bereken de fysieke absorptie (Het signaal op de detector)
        # Hint: je moet je alfa-berekening hier vectoriseren voor snelheid, 
        # maar voor het idee doe ik het even zo:
        detector_signal = np.zeros_like(t)
        
        # (In het echt wil je niet loopen over honderdduizenden punten, 
        # maar een numpy-array bewerking maken van je alfa_at_wavelength functie)
        print("Simuleren van laser interactie met gas...")
        for i in range(len(t)):
            detector_signal[i] = self.using_beer_lambert(initial_intensity, distance, wl_modulated[i])
        
        # 4. De Lock-in Demodulatie (Wiskunde)
        # Creëer de 2f referentie signalen (vaak X en Y componenten, we doen hier even versimpeld 1)
        ref_2f = np.cos(2 * np.pi * (2 * f_mod) * t)
        
        # Vermenigvuldig het detector signaal met de referentie (Mixen)
        mixed_signal = detector_signal * ref_2f
        
        # 5. Low-Pass Filter (Verwijder de snelle trillingen, behoud het DC-verloop)
        # We maken een simpel Butterworth filter
        nyq = 0.5 * fs
        cutoff = f_mod / 5  # Cutoff frequentie ruim onder de modulatie frequentie
        b, a = butter(4, cutoff / nyq, btype='low')
        
        # Pas het filter toe
        signal_2f = filtfilt(b, a, mixed_signal)
        
        # 6. Plot het resultaat
        plt.figure(figsize=(10, 5))
        plt.subplot(2, 1, 1)
        plt.plot(wl_ramp, detector_signal)
        plt.title("Detector Signaal (DC - Direct Absorption)")
        plt.ylabel("Intensiteit")
        
        plt.subplot(2, 1, 2)
        plt.plot(wl_ramp, signal_2f, color='red')
        plt.title("Gedemoduleerd 2f Signaal (Lock-in output)")
        plt.xlabel("Golflengte (nm)")
        #plt.xlim()
        #plt.ylim()
        plt.ylabel("2f Amplitude")
        
        plt.tight_layout()
        plt.show()

        return wl_ramp, signal_2f 
# example usage
beer_lambert = UseBeerLambert("C:/Users/Jaïr/OneDrive/Lectoraat/Spektrik/GasCell/Simulation/Measurement/methane_12_hitran_data.csv", concentration=0.1)

ini_intensity = 0.4 # intensity after 22 reflections
distance = 800 # in cm, 8 m
wavelength = 1654.0 # in nm
#final_intensity = beer_lambert.using_beer_lambert(initial_intensity=ini_intensity, distance=distance, wavelength=wavelength)
#print(final_intensity)

# sweep wavelengths
wavelength_range = np.linspace(1654.1, 1654.3, 100)
#beer_lambert.sweeping_wavelengths(initial_intensity=ini_intensity, distance=distance, wavelength_range=wavelength_range)
# simulate WMS 2f
wl_center = 1654.2
scan_width = 0.1
beer_lambert.simulate_wms_2f(initial_intensity=ini_intensity, distance=distance, wl_center=wl_center, scan_width=scan_width)
    