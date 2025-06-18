import wbdata
import pycountry
import json
from datetime import datetime

# Promedios regionales de camas hospitalarias por 1,000 habitantes (estimaciones OMS)
REGIONAL_HOSPITAL_BEDS = {
    'North America': 2.8,
    'Latin America': 2.1,
    'Europe': 5.0,
    'Africa': 0.5,
    'Asia': 2.5,
    'Oceania': 3.8
}

# Mapeo de países a regiones (simplificado, cubre todos los países)
COUNTRY_REGION = {country.alpha_2: 'Europe' if country.alpha_2 in ['DE', 'FR', 'IT', 'ES', 'GB', 'PL', 'RO', 'NL', 'BE', 'SE', 'AT', 'CH', 'PT', 'HU', 'FI']
                  else 'North America' if country.alpha_2 in ['US', 'CA', 'MX']
                  else 'Latin America' if country.alpha_2 in ['BR', 'AR', 'CO', 'PE', 'VE', 'CL', 'EC', 'BO', 'PY', 'UY', 'GY', 'SR']
                  else 'Africa' if country.alpha_2 in ['NG', 'ZA', 'KE', 'GH', 'ET', 'DZ', 'MA', 'EG', 'AO', 'SN']
                  else 'Asia' if country.alpha_2 in ['CN', 'IN', 'JP', 'KR', 'ID', 'SA', 'IR', 'IQ', 'MY', 'TH', 'VN', 'PK', 'BD', 'PH']
                  else 'Oceania' if country.alpha_2 in ['AU', 'NZ', 'FJ', 'PG']
                  else 'Asia' for country in pycountry.countries}

# Diccionario de nombres en español (extendido para cubrir más países)
SPANISH_NAMES = {
    'US': 'Estados Unidos', 'BR': 'Brasil', 'DE': 'Alemania', 'CN': 'China', 'IN': 'India', 'JP': 'Japón',
    'NG': 'Nigeria', 'FR': 'Francia', 'ZA': 'Sudáfrica', 'AU': 'Australia', 'CA': 'Canadá', 'MX': 'México',
    'GB': 'Reino Unido', 'IT': 'Italia', 'ES': 'España', 'AR': 'Argentina', 'CO': 'Colombia', 'PE': 'Perú',
    'VE': 'Venezuela', 'CL': 'Chile', 'EC': 'Ecuador', 'BO': 'Bolivia', 'PY': 'Paraguay', 'UY': 'Uruguay',
    'RU': 'Rusia', 'KR': 'Corea del Sur', 'ID': 'Indonesia', 'SA': 'Arabia Saudita', 'IR': 'Irán',
    'IQ': 'Irak', 'MY': 'Malasia', 'TH': 'Tailandia', 'VN': 'Vietnam', 'PK': 'Pakistán', 'BD': 'Bangladés',
    'PH': 'Filipinas', 'EG': 'Egipto', 'ET': 'Etiopía', 'KE': 'Kenia', 'GH': 'Ghana', 'DZ': 'Argelia',
    'MA': 'Marruecos', 'AO': 'Angola', 'SN': 'Senegal', 'NZ': 'Nueva Zelanda', 'PL': 'Polonia',
    'NL': 'Países Bajos', 'BE': 'Bélgica', 'SE': 'Suecia', 'AT': 'Austria', 'CH': 'Suiza', 'PT': 'Portugal',
    'HU': 'Hungría', 'FI': 'Finlandia', 'TR': 'Turquía', 'UA': 'Ucrania', 'SG': 'Singapur', 'NO': 'Noruega',
    'DK': 'Dinamarca', 'IE': 'Irlanda', 'CZ': 'Chequia', 'SK': 'Eslovaquia', 'HR': 'Croacia', 'RS': 'Serbia',
    'GR': 'Grecia', 'RO': 'Rumania', 'BG': 'Bulgaria', 'KZ': 'Kazajistán', 'UZ': 'Uzbekistán', 'AE': 'Emiratos Árabes Unidos'
    # Agrega más si necesitas nombres específicos para microestados
}

def get_population(country_code):
    """Obtiene la población de un país desde la API del Banco Mundial."""
    try:
        data = wbdata.get_data("SP.POP.TOTL", country=country_code)
        latest = max(data, key=lambda x: x['date'] if x['value'] else '0')
        return int(latest['value']) if latest['value'] else 100000  # Estimación mínima
    except:
        return 100000  # Estimación para microestados

def get_hospital_beds(country_code, population):
    """Obtiene o estima la capacidad hospitalaria (camas totales)."""
    try:
        data = wbdata.get_data("SH.MED.BEDS.ZS", country=country_code)
        latest = max(data, key=lambda x: x['date'] if x['value'] else '0')
        beds_per_1000 = latest['value'] if latest['value'] else REGIONAL_HOSPITAL_BEDS[COUNTRY_REGION.get(country_code, 'Asia')]
        return int(population * (beds_per_1000 / 1000))
    except:
        region = COUNTRY_REGION.get(country_code, 'Asia')
        return int(population * (REGIONAL_HOSPITAL_BEDS[region] / 1000))

def get_gdp(country_code):
    """Obtiene el PIB nominal en USD desde la API del Banco Mundial."""
    try:
        data = wbdata.get_data("NY.GDP.MKTP.CD", country=country_code)
        latest = max(data, key=lambda x: x['date'] if x['value'] else '0')
        return int(latest['value']) if latest['value'] else 1000000000  # Estimación mínima
    except:
        return 1000000000  # Estimación para microestados

def get_country_name(country_code):
    """Obtiene el nombre del país en español."""
    try:
        return SPANISH_NAMES.get(country_code, pycountry.countries.get(alpha_2=country_code).name)
    except:
        return country_code

def generate_countries_json():
    """Genera el JSON con datos de todos los países."""
    countries_data = {}
    
    for country in pycountry.countries:
        code = country.alpha_2
        if code in ['AQ', 'BV', 'TF', 'HM', 'GS']:  # Excluir territorios no soberanos
            continue
            
        population = get_population(code)
        hospital_capacity = get_hospital_beds(code, population)
        gdp = get_gdp(code)
        
        countries_data[code] = {
            "name": get_country_name(code),
            "population": population,
            "hospital_capacity": hospital_capacity,
            "gdp": gdp
        }
    
    print(f"Total de países incluidos: {len(countries_data)}")
    return countries_data

def main():
    """Genera y guarda el JSON."""
    data = generate_countries_json()
    
    # Guardar en archivo JSON
    with open('countries_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Archivo countries_data.json generado con éxito.")

if __name__ == "__main__":
    main()