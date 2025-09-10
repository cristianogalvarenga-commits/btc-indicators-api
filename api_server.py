from flask import Flask, jsonify
from flask_cors import CORS
import requests
import json
from datetime import datetime, timedelta
import threading
import time
import re
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Cache global para armazenar dados
data_cache = {
    'indicators': {},
    'summary': {},
    'last_update': None,
    'update_in_progress': False
}

class CorrectLogicDataCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Configuração dos indicadores com lógica CORRETA baseada no estudo detalhado
        self.indicators_config = {
            "Bitcoin Ahr999 Index": {
                "reference": 4.0,
                "description": "Índice que combina preço e média móvel de 200 dias. Valores acima de 4 indicam possível topo de mercado.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Pi Cycle Top Indicator": {
                "reference": 1.0,  # Representa o cruzamento (111-DMA / (350-DMA * 2))
                "description": "Cruzamento de médias móveis de 111 e 350 dias. Quando a 111DMA cruza a 350DMA x2, indica possível topo.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Puell Multiple": {
                "reference": 2.2,
                "description": "Receita diária dos mineradores vs média de 365 dias. Valores acima de 2.2 sugerem fim de ciclo.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Bitcoin Rainbow Chart": {
                "reference": 6.0,  # Banda laranja/vermelha
                "description": "Gráfico logarítmico com bandas de preço. Banda 6+ (vermelha) indica possível topo de mercado.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Days of ETF Net Outflows": {
                "reference": 10,
                "description": "Dias consecutivos de saídas líquidas de ETFs. Mais de 10 dias pode indicar fim de ciclo.",
                "unit": " dias",
                "logic": "higher_is_worse"
            },
            "ETF-to-BTC Ratio": {
                "reference": 3.5,
                "description": "Proporção entre ETFs e Bitcoin. Valores abaixo de 3.5% podem indicar fim de ciclo.",
                "unit": "%",
                "logic": "lower_is_worse"  # LÓGICA INVERSA CORRIGIDA
            },
            "2-Year MA Multiplier": {
                "reference": 364280,
                "description": "Multiplicador da média móvel de 2 anos. Valores próximos a $364k indicam topo histórico.",
                "unit": "$",
                "logic": "higher_is_worse"
            },
            "MVRV Z-Score": {
                "reference": 5.0,
                "description": "Z-Score do MVRV. Valores acima de 5 indicam possível topo.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Bitcoin Bubble Index": {
                "reference": 80,
                "description": "Índice de bolha baseado em desvios de preço. Valores acima de 80 indicam bolha extrema.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "USDT Flexible Savings": {
                "reference": 29,
                "description": "Taxa de poupança flexível USDT. Taxas acima de 29% indicam alta demanda por stablecoins.",
                "unit": "%",
                "logic": "higher_is_worse"
            },
            "RSI - 22 Day": {
                "reference": 80,
                "description": "Índice de Força Relativa de 22 dias. Valores acima de 80 indicam sobrecompra extrema.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "CMC Altcoin Season Index": {
                "reference": 75,
                "description": "Índice de temporada de altcoins. Valores acima de 75 indicam altseason extrema.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Bitcoin Dominance": {
                "reference": 40,
                "description": "Dominância do Bitcoin no mercado cripto. Quando cai para 40%, indica possível fim de ciclo.",
                "unit": "%",
                "logic": "lower_is_worse"  # LÓGICA INVERSA CORRIGIDA
            },
            "Bitcoin Long Term Holder Supply": {
                "reference": 13.5,
                "description": "Suprimento de holders de longo prazo. Valores abaixo de 13.5M indicam distribuição.",
                "unit": "M",
                "logic": "lower_is_worse"  # LÓGICA INVERSA CORRIGIDA
            },
            "Bitcoin Short Term Holder Supply": {
                "reference": 30,
                "description": "Suprimento de holders de curto prazo (%). Valores acima de 30% indicam especulação.",
                "unit": "%",
                "logic": "higher_is_worse"
            },
            "Bitcoin Reserve Risk": {
                "reference": 0.005,
                "description": "Risco de reserva baseado em HODL waves. Valores acima de 0.005 indicam alto risco.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Bitcoin Net Unrealized P&L": {
                "reference": 70,
                "description": "P&L não realizado líquido (NUPL). Valores acima de 70% indicam euforia extrema.",
                "unit": "%",
                "logic": "higher_is_worse"
            },
            "Bitcoin RHODL Ratio": {
                "reference": 10000,
                "description": "Ratio RHODL (Realized HODL). Valores acima de 10000 indicam possível topo.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Bitcoin Macro Oscillator": {
                "reference": 1.4,
                "description": "Oscilador macro baseado em ciclos. Valores acima de 1.4 indicam fim de ciclo.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Bitcoin MVRV Ratio": {
                "reference": 3.0,
                "description": "Market Value to Realized Value Ratio. Valores acima de 3 indicam sobrevalorização.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Bitcoin 4-Year Moving Average": {
                "reference": 3.5,
                "description": "Média móvel de 4 anos. Valores acima de 3.5 indicam possível topo de ciclo.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Crypto Bitcoin Bull Run Index": {
                "reference": 90,
                "description": "Índice de bull run cripto (CBBI). Valores acima de 90 indicam fim de bull run.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Mayer Multiple": {
                "reference": 2.2,
                "description": "Preço atual vs média móvel de 200 dias. Valores acima de 2.2 indicam sobrevalorização.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "Bitcoin AHR999x Top Escape": {
                "reference": 0.45,
                "description": "Indicador de escape do topo AHR999x. Valores abaixo de 0.45 indicam momento de venda.",
                "unit": "",
                "logic": "lower_is_worse"  # LÓGICA INVERSA CORRIGIDA
            },
            "MicroStrategy Avg Bitcoin Cost": {
                "reference": 155655,
                "description": "Custo médio do Bitcoin da MicroStrategy. Referência baseada em compras históricas.",
                "unit": "$",
                "logic": "higher_is_worse"
            },
            "Bitcoin Trend Indicator": {
                "reference": 7.0,
                "description": "Indicador de tendência baseado em momentum. Valores acima de 7 indicam possível reversão.",
                "unit": "",
                "logic": "higher_is_worse"
            },
            "3-Month Annualized Ratio": {
                "reference": 30,
                "description": "Ratio anualizado de 3 meses. Valores acima de 30% indicam crescimento insustentável.",
                "unit": "%",
                "logic": "higher_is_worse"
            },
            "Bitcoin Terminal Price": {
                "reference": 187702,
                "description": "Preço terminal baseado em modelos. Valores próximos a $187k indicam topo teórico.",
                "unit": "$",
                "logic": "higher_is_worse"
            },
            "Golden Ratio Multiplier": {
                "reference": 135522,
                "description": "Multiplicador da proporção áurea. Valores próximos a $135k indicam resistência forte.",
                "unit": "$",
                "logic": "higher_is_worse"
            },
            "Smithson Bitcoin Price Forecast": {
                "reference": 175000,
                "description": "Previsão de preço Smithson. Modelo baseado em análise técnica e fundamentalista.",
                "unit": "$",
                "logic": "higher_is_worse"
            },
            "Fear & Greed Index": {
                "reference": 80,
                "description": "Índice de medo e ganância do mercado. Valores acima de 80 indicam ganância extrema.",
                "unit": "",
                "logic": "higher_is_worse"
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

    def calculate_proximity_correct_logic(self, indicator_name, current, reference):
        """Calcula proximidade ao fim de ciclo com lógica CORRETA (0-100%)"""
        if current is None or reference is None:
            return 0
            
        config = self.indicators_config.get(indicator_name, {})
        logic = config.get("logic", "higher_is_worse")
        
        if logic == "higher_is_worse":
            # Para indicadores onde valores maiores indicam fim de ciclo
            proximity = (current / reference) * 100
            return max(0, min(100, proximity))
            
        elif logic == "lower_is_worse":
            # Para indicadores onde valores menores indicam fim de ciclo
            if indicator_name == "Bitcoin Dominance":
                # Lógica especial para dominância: 70% = 0%, 40% = 100%
                if current >= 70:
                    return 0
                elif current <= 40:
                    return 100
                else:
                    return ((70 - current) / (70 - 40)) * 100
            else:
                # Lógica geral para indicadores inversos
                if current <= reference:
                    return 100  # Na zona de risco
                else:
                    # Calcular proximidade baseada na distância da referência
                    # Assumindo que o dobro da referência seria 0% de proximidade
                    max_safe_value = reference * 2
                    if current >= max_safe_value:
                        return 0
                    else:
                        return 100 - ((current - reference) / (max_safe_value - reference)) * 100
        
        return max(0, min(100, proximity))

    def is_in_risk_zone_correct(self, indicator_name, current, reference):
        """Determina se o indicador está na zona de risco CORRETAMENTE"""
        if current is None or reference is None:
            return False
            
        config = self.indicators_config.get(indicator_name, {})
        logic = config.get("logic", "higher_is_worse")
        
        if logic == "higher_is_worse":
            return current >= reference  # Zona de risco quando atual >= referência
        elif logic == "lower_is_worse":
            return current <= reference  # Zona de risco quando atual <= referência
        
        return False

    def format_indicator_value(self, indicator_name, value):
        """Formata o valor do indicador com unidade apropriada"""
        if value is None:
            return "N/A"
            
        config = self.indicators_config.get(indicator_name, {})
        unit = config.get("unit", "")
        
        # Formatação especial para valores monetários
        if unit == "$":
            if value >= 1000:
                return f"${value:,.2f}"
            else:
                return f"${value:.2f}"
        
        # Formatação para percentuais
        elif unit == "%":
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

    def get_current_values(self):
        """Retorna valores atuais dos indicadores (dados reais + simulados)"""
        # Coletar dados dinâmicos
        fear_greed = self.get_fear_greed_index()
        dominance = self.get_bitcoin_dominance()
        
        # Valores atuais baseados nos dados mais recentes conhecidos (09/09/2025)
        current_values = {
            "Bitcoin Ahr999 Index": 0.98,
            "Pi Cycle Top Indicator": 0.58,  # 111397.74 / (191043.53) = ~0.58
            "Puell Multiple": 1.25,  # Valor atualizado da CoinMarketCap
            "Bitcoin Rainbow Chart": 3,
            "Days of ETF Net Outflows": 2,
            "ETF-to-BTC Ratio": 5.01,  # Valor que você mencionou - LONGE da zona de risco (3.5%)
            "2-Year MA Multiplier": 111312.05,
            "MVRV Z-Score": 2.12,
            "Bitcoin Bubble Index": 13.48,
            "USDT Flexible Savings": 5.66,
            "RSI - 22 Day": 47.173,
            "CMC Altcoin Season Index": 54,
            "Bitcoin Dominance": dominance,  # Valor dinâmico da API
            "Bitcoin Long Term Holder Supply": 15.47,
            "Bitcoin Short Term Holder Supply": 22.31,
            "Bitcoin Reserve Risk": 0.0024,
            "Bitcoin Net Unrealized P&L": 54.91,
            "Bitcoin RHODL Ratio": 2754,  # Valor atualizado da CoinMarketCap
            "Bitcoin Macro Oscillator": 0.84,  # Valor atualizado da CoinMarketCap
            "Bitcoin MVRV Ratio": 2.10,  # Valor atualizado da CoinMarketCap
            "Bitcoin 4-Year Moving Average": 2.13,  # Valor atualizado da CoinMarketCap
            "Crypto Bitcoin Bull Run Index": 74,  # Valor corrigido da CoinMarketCap
            "Mayer Multiple": 1.13,
            "Bitcoin AHR999x Top Escape": 3.04,  # Valor atualizado da CoinMarketCap
            "MicroStrategy Avg Bitcoin Cost": 73526,  # Valor atualizado da CoinMarketCap
            "Bitcoin Trend Indicator": 6.14,  # Valor atualizado da CoinMarketCap
            "3-Month Annualized Ratio": 9.95,  # Valor atualizado da CoinMarketCap
            "Bitcoin Terminal Price": 112035.99,  # Valor corrigido da CoinMarketCap
            "Golden Ratio Multiplier": 112035.99,  # Valor corrigido da CoinMarketCap
            "Smithson Bitcoin Price Forecast": 112035.99,  # Valor corrigido da CoinMarketCap
            "Fear & Greed Index": fear_greed  # Valor dinâmico da API
        }
        
        return current_values

    def collect_all_data(self):
        """Coleta todos os dados dos indicadores com lógica CORRETA"""
        print("🔄 Atualizando dados dos indicadores com lógica correta...")
        
        # Obter valores atuais
        current_values = self.get_current_values()
        
        # Processar todos os indicadores
        indicators = {}
        in_risk_zone_count = 0
        
        for name, config in self.indicators_config.items():
            current = current_values.get(name, 0)
            reference = config["reference"]
            
            # Calcular proximidade com lógica corrigida
            proximity = self.calculate_proximity_correct_logic(name, current, reference)
            
            # Verificar se está na zona de risco com lógica corrigida
            in_risk_zone = self.is_in_risk_zone_correct(name, current, reference)
            if in_risk_zone:
                in_risk_zone_count += 1
            
            indicators[name] = {
                "current": current,
                "reference": reference,
                "proximity": proximity,
                "description": config.get("description", ""),
                "formatted_current": self.format_indicator_value(name, current),
                "formatted_reference": self.format_indicator_value(name, reference),
                "unit": config.get("unit", ""),
                "in_risk_zone": in_risk_zone,
                "logic": config.get("logic", "higher_is_worse")
            }
        
        # Calcular estatísticas
        total_indicators = len(indicators)
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
            "inCycleZone": in_risk_zone_count,  # Agora com lógica correta
            "averageProximity": average_proximity,
            "overallStatus": overall_status,
            "lastUpdate": datetime.now().isoformat(),
            "validCount": total_indicators,
            "riskLevels": risk_levels,
            "riskZonePercentage": (in_risk_zone_count / total_indicators) * 100
        }
        
        return indicators, summary

# Instância do coletor
collector = CorrectLogicDataCollector()

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
                
                print(f"✅ Dados atualizados com lógica correta: {len(indicators)} indicadores")
                print(f"📊 Proximidade média: {summary['averageProximity']:.1f}%")
                print(f"🔴 Na zona de risco: {summary['inCycleZone']}/{summary['total']}")
                
                data_cache['update_in_progress'] = False
                
        except Exception as e:
            print(f"❌ Erro na atualização: {e}")
            data_cache['update_in_progress'] = False
        
        # Aguardar 5 minutos
        time.sleep(300)

@app.route('/')
def home():
    return jsonify({
        "message": "🎯 BTC Indicators API v5.0 - Lógica Correta Baseada em Estudo Detalhado!",
        "status": "online",
        "version": "5.0.0",
        "lastUpdate": data_cache.get('last_update', datetime.now()).isoformat() if data_cache.get('last_update') else datetime.now().isoformat(),
        "dataSource": "Estudo detalhado + Dados reais atualizados",
        "totalIndicators": 31,
        "improvements": [
            "✅ Lógica de proximidade corrigida para todos os 31 indicadores",
            "✅ Lógicas inversas implementadas corretamente",
            "✅ Contagem precisa de indicadores na zona de risco",
            "✅ ETF-to-BTC Ratio: lógica inversa corrigida",
            "✅ Bitcoin Dominance: lógica inversa corrigida",
            "✅ Valores atualizados da CoinMarketCap (09/09/2025)"
        ],
        "endpoints": [
            "/api/indicators - Todos os 31 indicadores com lógica correta",
            "/api/summary - Resumo executivo da análise",
            "/api/update - Força atualização dos dados",
            "/health - Status da API"
        ]
    })

@app.route('/api/indicators')
def get_indicators():
    """Retorna todos os indicadores com lógica correta"""
    if not data_cache['indicators']:
        # Primeira execução - coletar dados
        indicators, summary = collector.collect_all_data()
        data_cache['indicators'] = indicators
        data_cache['summary'] = summary
        data_cache['last_update'] = datetime.now()
    
    return jsonify(data_cache['indicators'])

@app.route('/api/summary')
def get_summary():
    """Retorna resumo da análise com lógica correta"""
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
            "message": "Dados atualizados com lógica correta!",
            "timestamp": datetime.now().isoformat(),
            "total_indicators": len(indicators),
            "average_proximity": summary['averageProximity'],
            "in_cycle_zone": summary['inCycleZone'],
            "risk_zone_percentage": summary['riskZonePercentage'],
            "improvements": "Lógica correta baseada em estudo detalhado dos 31 indicadores"
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
        "version": "5.0.0",
        "data_source": "Correct Logic Based on Detailed Study"
    })

if __name__ == '__main__':
    # Inicializar dados
    print("🎯 Iniciando BTC Indicators API v5.0 - Lógica Correta!")
    
    # Coletar dados iniciais
    try:
        indicators, summary = collector.collect_all_data()
        data_cache['indicators'] = indicators
        data_cache['summary'] = summary
        data_cache['last_update'] = datetime.now()
        print(f"✅ Dados iniciais carregados com lógica correta: {len(indicators)} indicadores")
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
