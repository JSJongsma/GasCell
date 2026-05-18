# CalculatingAlpha.py
# This folder contains a csv with the relevant data of the line intensity of methane between 1653 and 1655 nm. This data can 
# be used for the calculation of the absorption coefficient, alpha. This file will contain the function to do so.

import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd


class CalculateAlpha:
    def __init__(self, file_name, concentration=0.10, temperature=296, pressure_atm=1.0):
        self.file_name = file_name # string, path to the csv file containing the hitran data for methane
        self.temperature = temperature
        self.pressure_atm = pressure_atm
        self.concentration = concentration
        
    def load_hitran_data(self):
        # Laad de CSV in
        df = pd.read_csv(self.file_name)
        
        # Sorteer op golflengte (handig voor zoekopdrachten)
        df = df.sort_values('Wavelength_nm')
        
        # Optioneel: gooi extreem zwakke lijnen weg om geheugen te sparen
        # Bijv: alles onder 1e-27 cm/molecule
        df = df[df['Intensity_S'] > 1e-27]
        
        return df

    def calculate_alpha(self):
        """
        Berekent de absorptiecoëfficiënt alpha (cm^-1) voor elke lijn.
        Maakt gebruik van Lorentz-verbreding voor realistische atmosferische druk.
        
        Parameters:
        - temperature: temperatuur in Kelvin
        - pressure_atm: totale druk in de gascel in atm
        - concentration: de fractie van het te meten gas (bijv. 0.10 voor 10% methaan)
        """
        # 1. Constanten in CGS eenheden (cm, g, s)
        c = 2.99792458e10          # Lichtsnelheid in cm/s
        k_B = 1.380649e-16         # Boltzmann constante in erg/K (of dyn*cm/K)
        chemical_mass = 16.04 * 1.660539e-24  # Massa van CH4 molecuul in gram
        T_ref = 296.0              # HITRAN referentie temperatuur
        
        # 2. Bereken Getalsdichtheid (moleculen/cm^3)
        # P_cgs = totale druk in dyn/cm^2. 1 atm = 1,013,250 dyn/cm^2
        P_cgs = self.pressure_atm * 1.01325e6
        N_totaal = P_cgs / (k_B * self.temperature)
        
        # AANGEPAST: We nemen nu alleen de methaan moleculen
        N_methaan = N_totaal * self.concentration
        
        # 3. Data inladen
        # Let op: Zorg dat je read_csv op df_hitran doet in plaats van self.file_name opnieuw in te laden, 
        # aangezien je al een load_hitran_data() methode hebt gemaakt!
        df = self.load_hitran_data() 
        wavelengths = df['Wavelength_nm'].values
        line_intensities = df['Intensity_S'].values
        wavenumbers = df['Wavenumber_cm-1'].values
        gamma_airs = df['Gamma_Air'].values  # De cruciale kolom voor drukverbreding
        
        alpha = []
        
        for i in range(len(wavelengths)):
            # 4. Lorentz-verbreding berekenen (HWHM in cm^-1)
            # Formule: gamma(P, T) = gamma_0 * P * (T_ref/T)^n
            gamma_L = gamma_airs[i] * self.pressure_atm * (T_ref / self.temperature)**0.5
            
            # 5. Bereken alpha piek
            if gamma_L > 0:
                # Lorentz piek waarde: S * N_methaan / (pi * gamma_L)
                alpha_i = (line_intensities[i] * N_methaan) / (np.pi * gamma_L)
            else:
                # Fallback op Doppler als Gamma_Air ontbreekt of 0 is
                nu_0 = wavenumbers[i]
                delta_nu_D = (nu_0 / c) * np.sqrt(2 * k_B * self.temperature / chemical_mass)
                alpha_i = (line_intensities[i] * N_methaan) / (np.sqrt(np.pi) * delta_nu_D)
                
            alpha.append(alpha_i)
        
        return wavelengths, np.array(alpha)
    
    def plot_alpha(self, wavelengths, alpha):
        plt.figure(figsize=(10, 6))
        plt.plot(wavelengths, alpha, marker='o', linestyle='-', color='blue')
        plt.title('Absorptiecoëfficiënt Alpha voor Methaan (CH4)')
        plt.xlabel('Golflengte (nm)')
        plt.ylabel('Absorptiecoëfficiënt Alpha (cm^-1)')
        plt.grid(True)
        plt.xlim(1653, 1655)
        plt.ylim(0, max(alpha)*1.1)
        plt.show()

