from flask import Flask, jsonify
from flask_cors import CORS
import requests
import json
from datetime import datetime, timedelta
import threading
import time
import re

app = Flask(__name__)
CORS(app)

# Cache global para armazenar dados
data_cache = {
    'indicators': {},
    'summary': {},
    'last_update': None,
    'update_in_progress': False
}

class DynamicDataCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Configuração dos indicadores com dados simulados mais realistas
        self.indicators_data = {
            "Bitcoin Ahr999 Index": {"current": 1.00, "reference": 4, "description": "Índice que combina preço e média móvel de 200 dias"},
            "Pi Cycle Top Indicator": {"current": 111025.27, "reference": 189351.16, "description": "Cruzamento de médias móveis de 111 e 350 dias"},
            "Puell Multiple": {"current": 1.29, "reference": 2.2, "description": "Receita diária dos mineradores vs média de 365 dias"},
            "Bitcoin Rainbow Chart": {"current": 3, "reference": 5, "description": "Gráfico logarítmico com bandas de preço"},
            "Days of ETF Net Outflows": {"current": 0, "reference": 10, "description": "Dias consecutivos de saídas líquidas de ETFs"},
            "ETF-to-BTC Ratio": {"current": 4.94, "reference": 3.5, "description": "Proporção entre ETFs e Bitcoin"},
            "2-Year MA Multiplier": {"current": 110585.58, "reference": 361366, "description": "Multiplicador da média móvel de 2 anos"},
            "MVRV Z-Score": {"current": 2.10, "reference": 5, "description": "Z-Score do MVRV (Market Value to Realized Value)"},
            "Bitcoin Bubble Index": {"current": 13.48, "reference": 80, "description": "Índice de bolha baseado em desvios de preço"},
            "USDT Flexible Savings": {"current": 5.53, "reference": 29, "description": "Taxa de poupança flexível USDT"},
            "RSI - 22 Day": {"current": 46.52, "reference": 80, "description": "Índice de Força Relativa de 22 dias"},
            "CMC Altcoin Season Index": {"current": 49, "reference": 75, "description": "Índice de temporada de altcoins"},
            "Bitcoin Dominance": {"current": 57.82, "reference": 40, "description": "Dominância do Bitcoin no mercado cripto"},
            "Bitcoin Long Term Holder Supply": {"current": 15.48, "reference": 13.5, "description": "Suprimento de holders de longo prazo"},
            "Bitcoin Short Term Holder Supply": {"current": 22.27, "reference": 30, "description": "Suprimento de holders de curto prazo (%)"},
            "Bitcoin Reserve Risk": {"current": 0.0024, "reference": 0.005, "description": "Risco de reserva baseado em HODL waves"},
            "Bitcoin Net Unrealized P&L": {"current": 54.91, "reference": 70, "description": "P&L não realizado líquido (NUPL)"},
            "Bitcoin RHODL Ratio": {"current": 3315, "reference": 10000, "description": "Ratio RHODL (Realized HODL)"},
            "Bitcoin Macro Oscillator": {"current": 0.80, "reference": 1.4, "description": "Oscilador macro baseado em ciclos"},
            "Bitcoin MVRV Ratio": {"current": 2.08, "reference": 3, "description": "Market Value to Realized Value Ratio"},
            "Bitcoin 4-Year Moving Average": {"current": 2.10, "reference": 3.5, "description": "Média móvel de 4 anos"},
            "Crypto Bitcoin Bull Run Index": {"current": 76, "reference": 90, "description": "Índice de bull run cripto (CBBI)"},
            "Mayer Multiple": {"current": 1.13, "reference": 2.2, "description": "Preço atual vs média móvel de 200 dias"},
            "Bitcoin AHR999x Top Escape": {"current": 3.11, "reference": 0.45, "description": "Indicador de escape do topo AHR999x"},
            "MicroStrategy Avg Bitcoin Cost": {"current": 73526, "reference": 155655, "description": "Custo médio do Bitcoin da MicroStrategy"},
            "Bitcoin Trend Indicator": {"current": 6.14, "reference": 7, "description": "Indicador de tendência baseado em momentum"},
            "3-Month Annualized Ratio": {"current": 9.95, "reference": 30, "description": "Ratio anualizado de 3 meses"},
            "Bitcoin Terminal Price": {"current": 110585.58, "reference": 187702, "description": "Preço terminal baseado em modelos"},
            "Golden Ratio Multiplier": {"current": 110585.58, "reference": 135522, "description": "Multiplicador da proporção áurea"},
            "Smithson Bitcoin Price Forecast": {"current": 110585.58, "reference": 175000, "description": "Previsão de preço Smithson"},
            "Fear & Greed Index": {"current": 55, "reference": 80, "description": "Índice de medo e ganância do mercado"}
        }

    def get_fear_greed_index(self):
        """Coleta o índice Fear & Greed em tempo real"""
        try:
            url = "https://api.alternative.me/fng/"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data['data'][0]['value'])
        except Exception as e:
            print(f"Erro ao coletar Fear & Greed: {e}")
        return 55  # Valor padrão

    def get_bitcoin_dominance(self):
        """Coleta dominância do Bitcoin via API alternativa"""
        try:
            # Tentar API da CoinGecko
            url = "https://api.coingecko.com/api/v3/global"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                dominance = data['data']['market_cap_percentage']['btc']
                return float(dominance)
        except Exception as e:
            print(f"Erro ao coletar dominância: {e}")
        return 57.82  # Valor padrão

    def calculate_proximity(self, indicator_name, current, reference):
        """Calcula proximidade ao fim de ciclo (0-100%)"""
        if current is None or reference is None:
            return 0
            
        if indicator_name == "Bitcoin Dominance":
            # Lógica especial: quanto menor a dominância, mais próximo do topo
            if current >= 70:
                return 0
            elif current <= 40:
                return 100
            else:
                return ((70 - current) / (70 - 40)) * 100
        
        # Para indicadores onde valores maiores indicam fim de ciclo
        higher_is_worse_indicators = [
            "Bitcoin Ahr999 Index", "Pi Cycle Top Indicator", "Puell Multiple",
            "Bitcoin Rainbow Chart", "Days of ETF Net Outflows", "2-Year MA Multiplier",
            "MVRV Z-Score", "Bitcoin Bubble Index", "USDT Flexible Savings",
            "RSI - 22 Day", "CMC Altcoin Season Index", "Bitcoin Short Term Holder Supply",
            "Bitcoin Reserve Risk", "Bitcoin Net Unrealized P&L", "Bitcoin RHODL Ratio",
            "Bitcoin Macro Oscillator", "Bitcoin MVRV Ratio", "Bitcoin 4-Year Moving Average",
            "Crypto Bitcoin Bull Run Index", "Mayer Multiple", "MicroStrategy Avg Bitcoin Cost",
            "Bitcoin Trend Indicator", "3-Month Annualized Ratio", "Bitcoin Terminal Price",
            "Golden Ratio Multiplier", "Smithson Bitcoin Price Forecast", "Fear & Greed Index"
        ]
        
        if indicator_name in higher_is_worse_indicators:
            proximity = (current / reference) * 100
        else:
            # Para indicadores onde valores menores indicam fim de ciclo
            proximity = ((reference - current) / reference) * 100
            
        return max(0, min(100, proximity))

    def collect_all_data(self):
        """Coleta todos os dados dos indicadores"""
        print("🔄 Atualizando dados dos indicadores...")
        
        # Atualizar dados dinâmicos
        fear_greed = self.get_fear_greed_index()
        dominance = self.get_bitcoin_dominance()
        
        # Atualizar no dataset
        self.indicators_data["Fear & Greed Index"]["current"] = fear_greed
        self.indicators_data["Bitcoin Dominance"]["current"] = dominance
        
        # Calcular proximidades
        indicators = {}
        for name, data in self.indicators_data.items():
            proximity = self.calculate_proximity(name, data["current"], data["reference"])
            indicators[name] = {
                "current": data["current"],
                "reference": data["reference"],
                "proximity": proximity,
                "description": data.get("description", "")
            }
        
        # Calcular estatísticas
        total_indicators = len(indicators)
        in_cycle_zone = sum(1 for ind in indicators.values() if ind["proximity"] >= 70)
        average_proximity = sum(ind["proximity"] for ind in indicators.values()) / total_indicators
        
        # Status geral
        if average_proximity >= 80:
            overall_status = "🔴 ALTO RISCO - Possível fim de ciclo"
        elif average_proximity >= 60:
            overall_status = "🟡 MÉDIO RISCO - Monitorar de perto"
        elif average_proximity >= 40:
            overall_status = "🟠 BAIXO-MÉDIO RISCO - Início/meio do ciclo"
        else:
            overall_status = "🟢 BAIXO RISCO - Início/meio do ciclo"
        
        summary = {
            "total": total_indicators,
            "inCycleZone": in_cycle_zone,
            "averageProximity": average_proximity,
            "overallStatus": overall_status,
            "lastUpdate": datetime.now().isoformat(),
            "validCount": total_indicators
        }
        
        return indicators, summary

# Instância do coletor
collector = DynamicDataCollector()

def update_data_background():
    """Atualiza dados em background a cada 5 minutos"""
    while True:
        try:
            if not data_cache['update_in_progress']:
                data_cache['update_in_progress'] = True
                
                indicators, summary = collector.collect_all_data()
                
                data_cache['indicators'] = indicators
                data_cache['summary'] = summary
                data_cache['last_update'] = datetime.now()
                
                print(f"✅ Dados atualizados: {len(indicators)} indicadores, proximidade média: {summary['averageProximity']:.1f}%")
                
                data_cache['update_in_progress'] = False
                
        except Exception as e:
            print(f"❌ Erro na atualização: {e}")
            data_cache['update_in_progress'] = False
        
        # Aguardar 5 minutos
        time.sleep(300)

@app.route('/')
def home():
    return jsonify({
        "message": "🚀 BTC Indicators API está funcionando!",
        "status": "online",
        "version": "2.0.0",
        "lastUpdate": data_cache.get('last_update', datetime.now()).isoformat() if data_cache.get('last_update') else datetime.now().isoformat(),
        "endpoints": [
            "/api/indicators - Todos os indicadores analisados",
            "/api/summary - Resumo da análise",
            "/api/update - Força atualização dos dados",
            "/health - Status da API"
        ]
    })

@app.route('/api/indicators')
def get_indicators():
    """Retorna todos os indicadores com seus dados"""
    if not data_cache['indicators']:
        # Primeira execução - coletar dados
        indicators, summary = collector.collect_all_data()
        data_cache['indicators'] = indicators
        data_cache['summary'] = summary
        data_cache['last_update'] = datetime.now()
    
    return jsonify(data_cache['indicators'])

@app.route('/api/summary')
def get_summary():
    """Retorna resumo da análise"""
    if not data_cache['summary']:
        # Primeira execução - coletar dados
        indicators, summary = collector.collect_all_data()
        data_cache['indicators'] = indicators
        data_cache['summary'] = summary
        data_cache['last_update'] = datetime.now()
    
    return jsonify(data_cache['summary'])

@app.route('/api/update')
def force_update():
    """Força atualização dos dados"""
    try:
        indicators, summary = collector.collect_all_data()
        data_cache['indicators'] = indicators
        data_cache['summary'] = summary
        data_cache['last_update'] = datetime.now()
        
        return jsonify({
            "message": "Dados atualizados com sucesso!",
            "timestamp": datetime.now().isoformat(),
            "total_indicators": len(indicators),
            "average_proximity": summary['averageProximity']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Verifica status da API"""
    last_update = data_cache.get('last_update')
    is_recent = False
    
    if last_update:
        time_diff = datetime.now() - last_update
        is_recent = time_diff < timedelta(minutes=10)
    
    return jsonify({
        "status": "healthy" if is_recent else "stale",
        "last_update": last_update.isoformat() if last_update else None,
        "indicators_count": len(data_cache.get('indicators', {})),
        "update_in_progress": data_cache.get('update_in_progress', False)
    })

if __name__ == '__main__':
    # Inicializar dados
    print("🚀 Iniciando BTC Indicators API v2.0...")
    
    # Coletar dados iniciais
    try:
        indicators, summary = collector.collect_all_data()
        data_cache['indicators'] = indicators
        data_cache['summary'] = summary
        data_cache['last_update'] = datetime.now()
        print(f"✅ Dados iniciais carregados: {len(indicators)} indicadores")
    except Exception as e:
        print(f"⚠️ Erro ao carregar dados iniciais: {e}")
    
    # Iniciar thread de atualização em background
    update_thread = threading.Thread(target=update_data_background, daemon=True)
    update_thread.start()
    print("🔄 Thread de atualização automática iniciada")
    
    # Iniciar servidor
    print("🌐 Servidor iniciando na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
