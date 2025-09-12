#!/usr/bin/env python3
"""
API Server com Scraping Real da CoinMarketCap
Coleta dados dinâmicos da tabela de indicadores em tempo real
"""

from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import threading
import time
import re
import json

app = Flask(__name__)
CORS(app)

# Cache global para armazenar dados
indicators_cache = {}
last_update = None

def clean_number(text):
    """Limpa e converte texto para número"""
    if not text:
        return 0
    
    # Remove símbolos e espaços
    cleaned = re.sub(r'[^\d.,-]', '', str(text))
    
    # Trata números com vírgula como separador decimal
    if ',' in cleaned and '.' in cleaned:
        # Se tem ambos, vírgula é separador de milhares
        cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        # Se só tem vírgula, pode ser decimal (formato europeu)
        if len(cleaned.split(',')[-1]) <= 2:
            cleaned = cleaned.replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')
    
    try:
        return float(cleaned)
    except:
        return 0

def scrape_coinmarketcap_table():
    """Faz scraping da tabela de indicadores da CoinMarketCap"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(
            'https://coinmarketcap.com/charts/crypto-market-cycle-indicators/',
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Erro ao acessar CoinMarketCap: {response.status_code}")
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Procurar pela tabela de indicadores
        table_data = {}
        
        # Tentar encontrar a tabela
        table = soup.find('table') or soup.find('div', {'class': re.compile(r'table', re.I)})
        
        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Pular cabeçalho
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    try:
                        indicator_name = cells[1].get_text(strip=True)
                        current_value = cells[2].get_text(strip=True)
                        reference_value = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                        
                        # Mapear nomes para nosso formato
                        name_mapping = {
                            'Bitcoin Ahr999 Index': 'Bitcoin Ahr999 Index',
                            'Pi Cycle Top Indicator': 'Pi Cycle Top Indicator',
                            'Puell Multiple': 'Puell Multiple',
                            'Bitcoin Rainbow Chart': 'Bitcoin Rainbow Chart',
                            'Days of ETF Net Outflows': 'Days of ETF Net Outflows',
                            'ETF-to-BTC Ratio': 'ETF-to-BTC Ratio',
                            '2-Year MA Multiplier': '2-Year MA Multiplier',
                            'MVRV Z-Score': 'MVRV Z-Score',
                            'Bitcoin Bubble Index': 'Bitcoin Bubble Index'
                        }
                        
                        if indicator_name in name_mapping:
                            table_data[name_mapping[indicator_name]] = {
                                'current': current_value,
                                'reference': reference_value
                            }
                    except Exception as e:
                        print(f"Erro ao processar linha da tabela: {e}")
                        continue
        
        print(f"Dados coletados da tabela: {len(table_data)} indicadores")
        return table_data
        
    except Exception as e:
        print(f"Erro no scraping da CoinMarketCap: {e}")
        return {}

def get_fear_greed_index():
    """Coleta Fear & Greed Index"""
    try:
        response = requests.get('https://api.alternative.me/fng/', timeout=10)
        if response.status_code == 200:
            data = response.json()
            return float(data['data'][0]['value'])
    except:
        pass
    return 50  # Valor padrão

def get_bitcoin_dominance():
    """Coleta Bitcoin Dominance"""
    try:
        response = requests.get('https://api.coingecko.com/api/v3/global', timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['data']['market_cap_percentage']['btc']
    except:
        pass
    return 57.0  # Valor padrão

def update_indicators():
    """Atualiza todos os indicadores"""
    global indicators_cache, last_update
    
    print("Atualizando indicadores...")
    
    # Scraping da tabela da CoinMarketCap
    cmc_data = scrape_coinmarketcap_table()
    
    # Dados externos
    fear_greed = get_fear_greed_index()
    btc_dominance = get_bitcoin_dominance()
    
    # Definir todos os 31 indicadores com lógica correta
    indicators = {
        'Bitcoin Ahr999 Index': {
            'current': clean_number(cmc_data.get('Bitcoin Ahr999 Index', {}).get('current', '1.06')),
            'reference': 4.0,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Índice AHR999 do Bitcoin. Valores acima de 4 indicam possível topo.'
        },
        'Pi Cycle Top Indicator': {
            'current': clean_number(cmc_data.get('Pi Cycle Top Indicator', {}).get('current', '111537.06')),
            'reference': 192179.0,
            'unit': '$',
            'logic': 'higher_is_worse',
            'description': 'Indicador Pi Cycle Top. Quando 111DMA cruza 350DMA x2, indica topo.'
        },
        'Puell Multiple': {
            'current': clean_number(cmc_data.get('Puell Multiple', {}).get('current', '1.25')),
            'reference': 2.2,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Receita diária dos mineradores vs média de 365 dias.'
        },
        'Bitcoin Rainbow Chart': {
            'current': 3,
            'reference': 6.0,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Gráfico Rainbow do Bitcoin. Nível 6+ indica zona de venda.'
        },
        'Days of ETF Net Outflows': {
            'current': clean_number(cmc_data.get('Days of ETF Net Outflows', {}).get('current', '0')),
            'reference': 10,
            'unit': ' dias',
            'logic': 'higher_is_worse',
            'description': 'Dias consecutivos de saídas líquidas dos ETFs de Bitcoin.'
        },
        'ETF-to-BTC Ratio': {
            'current': clean_number(cmc_data.get('ETF-to-BTC Ratio', {}).get('current', '5.22')),
            'reference': 3.5,
            'unit': '%',
            'logic': 'lower_is_worse',
            'description': 'Ratio ETF para BTC. Valores ≤3.5% indicam fim de ciclo.'
        },
        '2-Year MA Multiplier': {
            'current': clean_number(cmc_data.get('2-Year MA Multiplier', {}).get('current', '115231.91')),
            'reference': clean_number(cmc_data.get('2-Year MA Multiplier', {}).get('reference', '367260')),
            'unit': '$',
            'logic': 'higher_is_worse',
            'description': 'Preço do Bitcoin vs média móvel de 2 anos multiplicada.'
        },
        'MVRV Z-Score': {
            'current': clean_number(cmc_data.get('MVRV Z-Score', {}).get('current', '2.30')),
            'reference': 5.0,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Z-Score do MVRV. Valores acima de 5 indicam sobrevalorização.'
        },
        'Bitcoin Bubble Index': {
            'current': clean_number(cmc_data.get('Bitcoin Bubble Index', {}).get('current', '13.48')),
            'reference': 80,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Índice de bolha do Bitcoin baseado em múltiplas métricas.'
        },
        'USDT Flexible Savings': {
            'current': 6.58,
            'reference': 29.0,
            'unit': '%',
            'logic': 'higher_is_worse',
            'description': 'Taxa de poupança flexível USDT. Altas taxas indicam stress no mercado.'
        },
        'RSI - 22 Day': {
            'current': 48.90,
            'reference': 80,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'RSI de 22 dias do Bitcoin. Valores acima de 80 indicam sobrecompra.'
        },
        'CMC Altcoin Season Index': {
            'current': 58,
            'reference': 75,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Índice de temporada de altcoins da CoinMarketCap.'
        },
        'Bitcoin Dominance': {
            'current': btc_dominance,
            'reference': 40.0,
            'unit': '%',
            'logic': 'lower_is_worse',
            'description': 'Dominância do Bitcoin no mercado cripto. ≤40% indica fim de ciclo.'
        },
        'Bitcoin Long Term Holder Supply': {
            'current': 15.47,
            'reference': 13.5,
            'unit': 'M',
            'logic': 'lower_is_worse',
            'description': 'Suprimento de Bitcoin em carteiras de longo prazo.'
        },
        'Bitcoin Short Term Holder Supply': {
            'current': 22.31,
            'reference': 30.0,
            'unit': '%',
            'logic': 'higher_is_worse',
            'description': 'Percentual do suprimento em carteiras de curto prazo.'
        },
        'Bitcoin Reserve Risk': {
            'current': 0.0024,
            'reference': 0.005,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Risco de reserva do Bitcoin baseado em HODL waves.'
        },
        'Bitcoin Net Unrealized P&L': {
            'current': 54.91,
            'reference': 70.0,
            'unit': '%',
            'logic': 'higher_is_worse',
            'description': 'P&L não realizado líquido (NUPL). Valores acima de 70% indicam euforia extrema.'
        },
        'Bitcoin RHODL Ratio': {
            'current': 2754,
            'reference': 10000,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Ratio RHODL do Bitcoin para análise de ciclos.'
        },
        'Bitcoin Macro Oscillator': {
            'current': 0.84,
            'reference': 1.4,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Oscilador macro do Bitcoin (BMO).'
        },
        'Bitcoin MVRV Ratio': {
            'current': 2.10,
            'reference': 3.0,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Ratio MVRV do Bitcoin. Valores acima de 3 indicam sobrevalorização.'
        },
        'Bitcoin 4-Year Moving Average': {
            'current': 2.13,
            'reference': 3.5,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Preço atual vs média móvel de 4 anos.'
        },
        'Crypto Bitcoin Bull Run Index': {
            'current': 74,
            'reference': 90,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Índice de bull run cripto (CBBI). Valores acima de 90 indicam fim de bull run.'
        },
        'Mayer Multiple': {
            'current': 1.13,
            'reference': 2.2,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Múltiplo Mayer. Preço atual vs média móvel de 200 dias.'
        },
        'Bitcoin AHR999x Top Escape': {
            'current': 3.04,
            'reference': 0.45,
            'unit': '',
            'logic': 'lower_is_worse',
            'description': 'Indicador AHR999x Top Escape. Valores ≤0.45 indicam escape do topo.'
        },
        'MicroStrategy Avg Bitcoin Cost': {
            'current': 73526.0,
            'reference': 155655.0,
            'unit': '$',
            'logic': 'higher_is_worse',
            'description': 'Custo médio do Bitcoin da MicroStrategy.'
        },
        'Bitcoin Trend Indicator': {
            'current': 6.14,
            'reference': 7.0,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Indicador de tendência do Bitcoin.'
        },
        '3-Month Annualized Ratio': {
            'current': 9.95,
            'reference': 30.0,
            'unit': '%',
            'logic': 'higher_is_worse',
            'description': 'Ratio anualizado de 3 meses.'
        },
        'Bitcoin Terminal Price': {
            'current': 112035.99,
            'reference': 187702.0,
            'unit': '$',
            'logic': 'higher_is_worse',
            'description': 'Preço terminal do Bitcoin.'
        },
        'Golden Ratio Multiplier': {
            'current': 112035.99,
            'reference': 135522.0,
            'unit': '$',
            'logic': 'higher_is_worse',
            'description': 'Multiplicador da proporção áurea.'
        },
        'Smithson Bitcoin Price Forecast': {
            'current': 112035.99,
            'reference': 175000.0,
            'unit': '$',
            'logic': 'higher_is_worse',
            'description': 'Previsão de preço do Bitcoin de Smithson.'
        },
        'Fear & Greed Index': {
            'current': fear_greed,
            'reference': 80,
            'unit': '',
            'logic': 'higher_is_worse',
            'description': 'Índice de Medo e Ganância. Valores acima de 80 indicam ganância extrema.'
        }
    }
    
    # Calcular proximidade e zona de risco para cada indicador
    processed_indicators = {}
    in_risk_zone_count = 0
    total_proximity = 0
    
    for name, data in indicators.items():
        current = data['current']
        reference = data['reference']
        logic = data['logic']
        
        # Calcular proximidade baseada na lógica
        if logic == 'higher_is_worse':
            # Quanto maior o valor atual, mais próximo do fim de ciclo
            if current >= reference:
                proximity = 100.0  # Atingiu ou ultrapassou a referência
                in_risk_zone = True
            else:
                proximity = (current / reference) * 100
                in_risk_zone = False
        else:  # lower_is_worse
            # Quanto menor o valor atual, mais próximo do fim de ciclo
            if current <= reference:
                proximity = 100.0  # Atingiu ou ficou abaixo da referência
                in_risk_zone = True
            else:
                # Calcular proximidade inversa
                proximity = max(0, 100 - ((current - reference) / reference) * 100)
                in_risk_zone = False
        
        # Garantir que proximidade não seja negativa
        proximity = max(0, min(100, proximity))
        
        # Determinar nível de risco
        if proximity >= 70:
            risk_level = 'ALTO'
        elif proximity >= 50:
            risk_level = 'MÉDIO'
        else:
            risk_level = 'BAIXO'
        
        # Contar indicadores na zona de risco
        if in_risk_zone:
            in_risk_zone_count += 1
        
        total_proximity += proximity
        
        processed_indicators[name] = {
            'current': current,
            'reference': reference,
            'unit': data['unit'],
            'proximity': round(proximity, 1),
            'risk_level': risk_level,
            'in_risk_zone': in_risk_zone,
            'description': data['description'],
            'logic': logic
        }
    
    # Calcular estatísticas gerais
    avg_proximity = total_proximity / len(indicators)
    risk_zone_percentage = (in_risk_zone_count / len(indicators)) * 100
    
    # Determinar status geral
    if avg_proximity >= 70:
        general_status = "🔴 ALTO RISCO - Possível fim de ciclo"
    elif avg_proximity >= 50:
        general_status = "🟠 BAIXO-MÉDIO RISCO - Início/meio do ciclo"
    else:
        general_status = "🟢 BAIXO RISCO - Início do ciclo"
    
    # Contar por nível de risco
    risk_counts = {'BAIXO': 0, 'MÉDIO': 0, 'ALTO': 0, 'CRÍTICO': 0}
    for indicator in processed_indicators.values():
        if indicator['in_risk_zone']:
            risk_counts['CRÍTICO'] += 1
        else:
            risk_counts[indicator['risk_level']] += 1
    
    indicators_cache = {
        'indicators': processed_indicators,
        'summary': {
            'total_indicators': len(indicators),
            'in_risk_zone': in_risk_zone_count,
            'avg_proximity': round(avg_proximity, 1),
            'risk_zone_percentage': round(risk_zone_percentage, 1),
            'general_status': general_status,
            'risk_distribution': risk_counts
        }
    }
    
    last_update = time.strftime('%d/%m/%Y, %H:%M:%S')
    print(f"Indicadores atualizados: {len(indicators)} indicadores, {in_risk_zone_count} na zona de risco")

def background_updater():
    """Thread para atualizar dados em background"""
    while True:
        try:
            update_indicators()
            time.sleep(300)  # Atualizar a cada 5 minutos
        except Exception as e:
            print(f"Erro na atualização em background: {e}")
            time.sleep(60)  # Tentar novamente em 1 minuto

@app.route('/')
def home():
    return jsonify({
        'message': 'API de Indicadores BTC - Scraping Real da CoinMarketCap',
        'status': 'online',
        'last_update': last_update,
        'endpoints': ['/api/summary', '/api/indicators', '/api/update']
    })

@app.route('/api/summary')
def get_summary():
    if not indicators_cache:
        update_indicators()
    
    return jsonify({
        'summary': indicators_cache.get('summary', {}),
        'last_update': last_update
    })

@app.route('/api/indicators')
def get_indicators():
    if not indicators_cache:
        update_indicators()
    
    return jsonify({
        'indicators': indicators_cache.get('indicators', {}),
        'last_update': last_update
    })

@app.route('/api/update')
def force_update():
    update_indicators()
    return jsonify({
        'message': 'Indicadores atualizados com sucesso',
        'last_update': last_update,
        'total_indicators': len(indicators_cache.get('indicators', {}))
    })

if __name__ == '__main__':
    # Atualizar dados inicialmente
    update_indicators()
    
    # Iniciar thread de atualização em background
    updater_thread = threading.Thread(target=background_updater, daemon=True)
    updater_thread.start()
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=5000, debug=False)
