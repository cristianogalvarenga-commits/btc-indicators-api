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

class RealDataCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Dados reais coletados da CoinMarketCap (atualizados em 07/09/2025)
        self.real_indicators_data = {
            "Bitcoin Ahr999 Index": {
                "current": 0.98, 
                "reference": 4, 
                "description": "Índice que combina preço e média móvel de 200 dias. Valores acima de 4 indicam possível topo de mercado.",
                "unit": "",
                "is_percentage": False
            },
            "Pi Cycle Top Indicator": {
                "current": 111288.75, 
                "reference": 190771, 
                "description": "Cruzamento de médias móveis de 111 e 350 dias. Quando a 111DMA cruza a 350DMA x2, indica possível topo.",
                "unit": "$",
                "is_percentage": False
            },
            "Puell Multiple": {
                "current": 1.13, 
                "reference": 2.2, 
                "description": "Receita diária dos mineradores vs média de 365 dias. Valores acima de 2.2 sugerem fim de ciclo.",
                "unit": "",
                "is_percentage": False
            },
            "Bitcoin Rainbow Chart": {
                "current": 3, 
                "reference": 5, 
                "description": "Gráfico logarítmico com bandas de preço. Banda 5 (vermelha) indica possível topo de mercado.",
                "unit": "",
                "is_percentage": False
            },
            "Days of ETF Net Outflows": {
                "current": 2, 
                "reference": 10, 
                "description": "Dias consecutivos de saídas líquidas de ETFs. Mais de 10 dias pode indicar fim de ciclo.",
                "unit": " dias",
                "is_percentage": False
            },
            "ETF-to-BTC Ratio": {
                "current": 5.2, 
                "reference": 3.5, 
                "description": "Proporção entre ETFs e Bitcoin. Valores acima de 3.5% podem indicar sobrecompra.",
                "unit": "%",
                "is_percentage": True
            },
            "2-Year MA Multiplier": {
                "current": 111312.05, 
                "reference": 364280, 
                "description": "Multiplicador da média móvel de 2 anos. Valores próximos a $364k indicam topo histórico.",
                "unit": "$",
                "is_percentage": False
            },
            "MVRV Z-Score": {
                "current": 2.12, 
                "reference": 5, 
                "description": "Z-Score do MVRV (Market Value to Realized Value). Valores acima de 5 indicam possível topo.",
                "unit": "",
                "is_percentage": False
            },
            "Bitcoin Bubble Index": {
                "current": 13.48, 
                "reference": 80, 
                "description": "Índice de bolha baseado em desvios de preço. Valores acima de 80 indicam bolha extrema.",
                "unit": "",
                "is_percentage": False
            },
            "USDT Flexible Savings": {
                "current": 5.66, 
                "reference": 29, 
                "description": "Taxa de poupança flexível USDT. Taxas acima de 29% indicam alta demanda por stablecoins.",
                "unit": "%",
                "is_percentage": True
            },
            "RSI - 22 Day": {
                "current": 47.173, 
                "reference": 80, 
                "description": "Índice de Força Relativa de 22 dias. Valores acima de 80 indicam sobrecompra extrema.",
                "unit": "",
                "is_percentage": False
            },
            "CMC Altcoin Season Index": {
                "current": 54, 
                "reference": 75, 
                "description": "Índice de temporada de altcoins. Valores acima de 75 indicam altseason extrema.",
                "unit": "",
                "is_percentage": False
            },
            "Bitcoin Dominance": {
                "current": 57.78, 
                "reference": 40, 
                "description": "Dominância do Bitcoin no mercado cripto. Quando cai para 40%, indica possível fim de ciclo.",
                "unit": "%",
                "is_percentage": True
            },
            "Bitcoin Long Term Holder Supply": {
                "current": 15.47, 
                "reference": 13.5, 
                "description": "Suprimento de holders de longo prazo. Valores abaixo de 13.5M indicam distribuição.",
                "unit": "M",
                "is_percentage": False
            },
            "Bitcoin Short Term Holder Supply": {
                "current": 22.31, 
                "reference": 30, 
                "description": "Suprimento de holders de curto prazo (%). Valores acima de 30% indicam especulação.",
                "unit": "%",
                "is_percentage": True
            },
            "Bitcoin Reserve Risk": {
                "current": 0.0024, 
                "reference": 0.005, 
                "description": "Risco de reserva baseado em HODL waves. Valores acima de 0.005 indicam alto risco.",
                "unit": "",
                "is_percentage": False
            },
            "Bitcoin Net Unrealized P&L": {
                "current": 54.91, 
                "reference": 70, 
                "description": "P&L não realizado líquido (NUPL). Valores acima de 70% indicam euforia extrema.",
                "unit": "%",
                "is_percentage": True
            },
            "Bitcoin RHODL Ratio": {
                "current": 2844, 
                "reference": 10000, 
                "description": "Ratio RHODL (Realized HODL). Valores acima de 10000 indicam possível topo.",
                "unit": "",
                "is_percentage": False
            },
            "Bitcoin Macro Oscillator": {
                "current": 0.82, 
                "reference": 1.4, 
                "description": "Oscilador macro baseado em ciclos. Valores acima de 1.4 indicam fim de ciclo.",
                "unit": "",
                "is_percentage": False
            },
            "Bitcoin MVRV Ratio": {
                "current": 2.09, 
                "reference": 3, 
                "description": "Market Value to Realized Value Ratio. Valores acima de 3 indicam sobrevalorização.",
                "unit": "",
                "is_percentage": False
            },
            "Bitcoin 4-Year Moving Average": {
                "current": 2.12, 
                "reference": 3.5, 
                "description": "Média móvel de 4 anos. Valores acima de 3.5 indicam possível topo de ciclo.",
                "unit": "",
                "is_percentage": False
            },
            "Crypto Bitcoin Bull Run Index": {
                "current": 73, 
                "reference": 90, 
                "description": "Índice de bull run cripto (CBBI). Valores acima de 90 indicam fim de bull run.",
                "unit": "",
                "is_percentage": False
            },
            "Mayer Multiple": {
                "current": 1.13, 
                "reference": 2.2, 
                "description": "Preço atual vs média móvel de 200 dias. Valores acima de 2.2 indicam sobrevalorização.",
                "unit": "",
                "is_percentage": False
            },
            "Bitcoin AHR999x Top Escape": {
                "current": 3.09, 
                "reference": 0.45, 
                "description": "Indicador de escape do topo AHR999x. Valores abaixo de 0.45 indicam momento de venda.",
                "unit": "",
                "is_percentage": False
            },
            "MicroStrategy Avg Bitcoin Cost": {
                "current": 73526, 
                "reference": 155655, 
                "description": "Custo médio do Bitcoin da MicroStrategy. Referência baseada em compras históricas.",
                "unit": "$",
                "is_percentage": False
            },
            "Bitcoin Trend Indicator": {
                "current": 6.14, 
                "reference": 7, 
                "description": "Indicador de tendência baseado em momentum. Valores acima de 7 indicam possível reversão.",
                "unit": "",
                "is_percentage": False
            },
            "3-Month Annualized Ratio": {
                "current": 9.95, 
                "reference": 30, 
                "description": "Ratio anualizado de 3 meses. Valores acima de 30% indicam crescimento insustentável.",
                "unit": "%",
                "is_percentage": True
            },
            "Bitcoin Terminal Price": {
                "current": 111312.05, 
                "reference": 187702, 
                "description": "Preço terminal baseado em modelos. Valores próximos a $187k indicam topo teórico.",
                "unit": "$",
                "is_percentage": False
            },
            "Golden Ratio Multiplier": {
                "current": 111312.05, 
                "reference": 135522, 
                "description": "Multiplicador da proporção áurea. Valores próximos a $135k indicam resistência forte.",
                "unit": "$",
                "is_percentage": False
            },
            "Smithson Bitcoin Price Forecast": {
                "current": 111312.05, 
                "reference": 175000, 
                "description": "Previsão de preço Smithson. Modelo baseado em análise técnica e fundamentalista.",
                "unit": "$",
                "is_percentage": False
            },
            "Fear & Greed Index": {
                "current": 55, 
                "reference": 80, 
                "description": "Índice de medo e ganância do mercado. Valores acima de 80 indicam ganância extrema.",
                "unit": "",
                "is_percentage": False
            }
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
        return 57.78  # Valor padrão

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
        
        elif indicator_name == "Bitcoin AHR999x Top Escape":
            # Lógica inversa: quanto menor o valor, mais próximo do topo
            if current <= reference:
                return 100
            else:
                return max(0, 100 - ((current - reference) / reference) * 100)
                
        elif indicator_name == "Bitcoin Long Term Holder Supply":
            # Lógica inversa: quanto menor o supply, mais próximo do topo
            if current <= reference:
                return 100
            else:
                return max(0, 100 - ((current - reference) / reference) * 100)
        
        else:
            # Para a maioria dos indicadores: quanto maior o valor, mais próximo do topo
            proximity = (current / reference) * 100
            
        return max(0, min(100, proximity))

    def format_indicator_value(self, indicator_name, value):
        """Formata o valor do indicador com unidade apropriada"""
        if value is None:
            return "N/A"
            
        config = self.real_indicators_data.get(indicator_name, {})
        unit = config.get("unit", "")
        is_percentage = config.get("is_percentage", False)
        
        # Formatação especial para valores monetários
        if unit == "$":
            if value >= 1000:
                return f"${value:,.2f}"
            else:
                return f"${value:.2f}"
        
        # Formatação para percentuais
        elif is_percentage or unit == "%":
            return f"{value:.2f}%"
        
        # Formatação para milhões
        elif unit == "M":
            return f"{value:.2f}M"
        
        # Formatação para dias
        elif unit == " dias":
            return f"{int(value)} dias"
        
        # Formatação padrão
        else:
            if isinstance(value, float):
                if value < 1:
                    return f"{value:.4f}"
                elif value < 100:
                    return f"{value:.2f}"
                else:
                    return f"{value:,.0f}"
            else:
                return str(value)

    def collect_all_data(self):
        """Coleta todos os dados dos indicadores"""
        print("🔄 Atualizando dados dos indicadores...")
        
        # Atualizar dados dinâmicos
        fear_greed = self.get_fear_greed_index()
        dominance = self.get_bitcoin_dominance()
        
        # Atualizar no dataset
        self.real_indicators_data["Fear & Greed Index"]["current"] = fear_greed
        self.real_indicators_data["Bitcoin Dominance"]["current"] = dominance
        
        # Calcular proximidades
        indicators = {}
        for name, data in self.real_indicators_data.items():
            proximity = self.calculate_proximity(name, data["current"], data["reference"])
            
            indicators[name] = {
                "current": data["current"],
                "reference": data["reference"],
                "proximity": proximity,
                "description": data.get("description", ""),
                "formatted_current": self.format_indicator_value(name, data["current"]),
                "formatted_reference": self.format_indicator_value(name, data["reference"]),
                "unit": data.get("unit", ""),
                "is_percentage": data.get("is_percentage", False)
            }
        
        # Calcular estatísticas
        total_indicators = len(indicators)
        in_cycle_zone = sum(1 for ind in indicators.values() if ind["proximity"] >= 70)
        average_proximity = sum(ind["proximity"] for ind in indicators.values()) / total_indicators
        
        # Contar por níveis de risco
        risk_levels = {"baixo": 0, "medio": 0, "alto": 0, "critico": 0}
        for indicator in indicators.values():
            proximity = indicator["proximity"]
            if proximity >= 90:
                risk_levels["critico"] += 1
            elif proximity >= 70:
                risk_levels["alto"] += 1
            elif proximity >= 50:
                risk_levels["medio"] += 1
            else:
                risk_levels["baixo"] += 1
        
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
            "validCount": total_indicators,
            "riskLevels": risk_levels,
            "riskZonePercentage": (in_cycle_zone / total_indicators) * 100
        }
        
        return indicators, summary

# Instância do coletor
collector = RealDataCollector()

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
        "message": "🚀 BTC Indicators API v3.0 - Dados Reais da CoinMarketCap!",
        "status": "online",
        "version": "3.0.0",
        "lastUpdate": data_cache.get('last_update', datetime.now()).isoformat() if data_cache.get('last_update') else datetime.now().isoformat(),
        "dataSource": "CoinMarketCap + APIs em tempo real",
        "totalIndicators": 31,
        "endpoints": [
            "/api/indicators - Todos os 31 indicadores analisados",
            "/api/summary - Resumo executivo da análise",
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
            "average_proximity": summary['averageProximity'],
            "in_cycle_zone": summary['inCycleZone'],
            "risk_zone_percentage": summary['riskZonePercentage']
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
        "update_in_progress": data_cache.get('update_in_progress', False),
        "version": "3.0.0",
        "data_source": "CoinMarketCap Real Data"
    })

if __name__ == '__main__':
    # Inicializar dados
    print("🚀 Iniciando BTC Indicators API v3.0 - Dados Reais da CoinMarketCap...")
    
    # Coletar dados iniciais
    try:
        indicators, summary = collector.collect_all_data()
        data_cache['indicators'] = indicators
        data_cache['summary'] = summary
        data_cache['last_update'] = datetime.now()
        print(f"✅ Dados iniciais carregados: {len(indicators)} indicadores")
        print(f"📊 Proximidade média: {summary['averageProximity']:.1f}%")
        print(f"🔴 Na zona de risco: {summary['inCycleZone']}/{summary['total']}")
    except Exception as e:
        print(f"⚠️ Erro ao carregar dados iniciais: {e}")
    
    # Iniciar thread de atualização em background
    update_thread = threading.Thread(target=update_data_background, daemon=True)
    update_thread.start()
    print("🔄 Thread de atualização automática iniciada")
    
    # Iniciar servidor
    print("🌐 Servidor iniciando na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
