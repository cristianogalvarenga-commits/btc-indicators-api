from flask import Flask, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import requests
import threading
import time

app = Flask(__name__)
CORS(app)

class BTCIndicatorsAPI:
    def __init__(self):
        self.data_file = os.path.join(os.getcwd(), 'indicators_data.json') # Caminho absoluto
        self.last_update = None
        self.indicators_data = {}
        self.load_data()
        
    def load_data(self):
        """Carrega dados do arquivo JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.indicators_data = data.get('indicators', {})
                    self.last_update = data.get('last_update')
            else:
                self.initialize_default_data()
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            self.initialize_default_data()
    
    def initialize_default_data(self):
        """Inicializa com dados padrão baseados na CoinMarketCap"""
        self.indicators_data = {
            "Bitcoin Ahr999 Index": {
                "current": 1.12,
                "reference": 4.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Indica sobrecompra quando >= 4.0"
            },
            "Pi Cycle Top Indicator": {
                "current": 109127.96,
                "reference": 184998.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Sinal de topo quando 111DMA cruza 350DMA x2"
            },
            "Puell Multiple": {
                "current": 1.35,
                "reference": 2.2,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Receita dos mineradores vs média histórica"
            },
            "Bitcoin Rainbow Chart": {
                "current": 3.0,
                "reference": 5.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Nível de preço no gráfico arco-íris"
            },
            "Days of ETF Net Outflows": {
                "current": 2.0,
                "reference": 10.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Dias consecutivos de saída de ETFs"
            },
            "ETF-to-BTC Ratio": {
                "current": 5.15,
                "reference": 3.5,
                "compare": "<=",
                "source": "coinmarketcap",
                "description": "Proporção de ETFs vs BTC total"
            },
            "2-Year MA Multiplier": {
                "current": 115657.25,
                "reference": 353164.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Preço vs média móvel de 2 anos"
            },
            "MVRV Z-Score": {
                "current": 2.42,
                "reference": 5.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Valor de mercado vs valor realizado"
            },
            "Bitcoin Bubble Index": {
                "current": 13.48,
                "reference": 80.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Índice de bolha especulativa"
            },
            "USDT Flexible Savings": {
                "current": 5.78,
                "reference": 29.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Taxa de poupança flexível USDT"
            },
            "RSI - 22 Day": {
                "current": 49.418,
                "reference": 80.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Índice de força relativa 22 dias"
            },
            "CMC Altcoin Season Index": {
                "current": 43.0,
                "reference": 75.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Índice de temporada de altcoins"
            },
            "Bitcoin Dominance": {
                "current": 58.97,
                "reference": 65.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Dominância do Bitcoin no mercado"
            },
            "Bitcoin Long Term Holder Supply": {
                "current": 15.65,
                "reference": 13.5,
                "compare": "<=",
                "source": "coinmarketcap",
                "description": "Oferta de holders de longo prazo"
            },
            "Bitcoin Short Term Holder Supply (%)": {
                "current": 21.39,
                "reference": 30.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Oferta de holders de curto prazo"
            },
            "Bitcoin Reserve Risk": {
                "current": 0.0026,
                "reference": 0.005,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Risco de reserva dos holders"
            },
            "Bitcoin Net Unrealized P&L (NUPL)": {
                "current": 54.91,
                "reference": 70.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Lucro/prejuízo não realizado líquido"
            },
            "Bitcoin RHODL Ratio": {
                "current": 3518.0,
                "reference": 10000.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Ratio RHODL para timing de ciclo"
            },
            "Bitcoin Macro Oscillator (BMO)": {
                "current": 0.98,
                "reference": 1.4,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Oscilador macro do Bitcoin"
            },
            "Bitcoin MVRV Ratio": {
                "current": 2.23,
                "reference": 3.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Market Value to Realized Value"
            },
            "Bitcoin 4-Year Moving Average": {
                "current": 2.26,
                "reference": 3.5,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Média móvel de 4 anos"
            },
            "Crypto Bitcoin Bull Run Index (CBBI)": {
                "current": 79.0,
                "reference": 90.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Índice de bull run do Bitcoin"
            },
            "Mayer Multiple": {
                "current": 1.18,
                "reference": 2.2,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Preço vs média móvel de 200 dias"
            },
            "Bitcoin AHR999x Top Escape Indicator": {
                "current": 2.69,
                "reference": 0.45,
                "compare": "<=",
                "source": "coinmarketcap",
                "description": "Indicador de escape do topo"
            },
            "MicroStrategy's Avg Bitcoin Cost": {
                "current": 73271.0,
                "reference": 155655.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Custo médio do Bitcoin da MicroStrategy"
            },
            "Bitcoin Trend Indicator": {
                "current": 6.14,
                "reference": 7.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Indicador de tendência do Bitcoin"
            },
            "3-Month Annualized Ratio": {
                "current": 9.95,
                "reference": 30.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Ratio anualizado de 3 meses"
            },
            "Bitcoin Terminal Price": {
                "current": 115657.25,
                "reference": 187702.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Preço terminal projetado"
            },
            "Golden Ratio Multiplier": {
                "current": 115657.25,
                "reference": 135522.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Multiplicador da proporção áurea"
            },
            "Smithson's Bitcoin Price Forecast": {
                "current": 115657.25,
                "reference": 175000.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Previsão de preço do Smithson"
            },
            "Fear & Greed Index": {
                "current": 50.0,  # Será atualizado via API
                "reference": 90.0,
                "compare": ">=",
                "source": "api",
                "description": "Índice de medo e ganância do mercado"
            }
        }
        self.save_data()
    
    def get_fear_greed_index(self):
        """Coleta o Fear & Greed Index da API"""
        try:
            print("📊 Coletando Fear & Greed Index...")
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                value = float(data['data'][0]['value'])
                self.indicators_data["Fear & Greed Index"]["current"] = value
                print(f"   Fear & Greed Index: {value}")
                return value
        except Exception as e:
            print(f"❌ Erro ao coletar Fear & Greed Index: {e}")
        return None
    
    def calculate_proximity(self, current, reference, compare_type):
        """Calcula a proximidade ao topo"""
        if current is None or reference is None:
            return None
        
        try:
            if compare_type == ">=":
                if current >= reference:
                    return 100.0
                else:
                    return (current / reference) * 100
            else:  # "<="
                if current <= reference:
                    return 100.0
                else:
                    return (reference / current) * 100
        except (ZeroDivisionError, TypeError):
            return None
    
    def analyze_indicators(self):
        """Análise completa de todos os indicadores"""
        print(f"🚀 [{datetime.now()}] Iniciando análise dos indicadores BTC...")
        
        # Atualizar Fear & Greed Index
        self.get_fear_greed_index()
        
        # Calcular estatísticas
        in_cycle_count = 0
        total_proximity = 0
        valid_count = 0
        results = []
        
        for name, data in self.indicators_data.items():
            current = data.get('current')
            reference = data.get('reference')
            compare_type = data.get('compare', '>=')
            source = data.get('source', 'unknown')
            description = data.get('description', '')
            
            proximity = self.calculate_proximity(current, reference, compare_type)
            in_cycle_zone = False
            
            if proximity is not None:
                if proximity >= 100:
                    in_cycle_zone = True
                    in_cycle_count += 1
                
                total_proximity += proximity
                valid_count += 1
            
            results.append({
                'name': name,
                'current': current,
                'reference': reference,
                'proximity': proximity,
                'inCycleZone': in_cycle_zone,
                'compare': compare_type,
                'source': source,
                'description': description
            })
        
        # Calcular média
        average_proximity = total_proximity / valid_count if valid_count > 0 else 0
        
        # Status geral
        if average_proximity >= 85:
            overall_status = "🔴 ALTO RISCO - Possível fim de ciclo próximo"
        elif average_proximity >= 70:
            overall_status = "🟡 MÉDIO RISCO - Monitorar de perto"
        elif average_proximity >= 50:
            overall_status = "🟠 ATENÇÃO - Ciclo avançando"
        else:
            overall_status = "🟢 BAIXO RISCO - Início/meio do ciclo"
        
        summary = {
            'inCycleZone': in_cycle_count,
            'total': len(self.indicators_data),
            'validCount': valid_count,
            'averageProximity': average_proximity,
            'lastUpdate': datetime.now().isoformat(),
            'overallStatus': overall_status
        }
        
        self.last_update = datetime.now().isoformat()
        self.save_data()
        
        print(f"✅ Análise concluída: {in_cycle_count}/{valid_count} na zona, média {average_proximity:.1f}%")
        
        return {
            'indicators': results,
            'summary': summary
        }
    
    def save_data(self):
        """Salva dados no arquivo JSON"""
        try:
            data = {
                'indicators': self.indicators_data,
                'last_update': self.last_update or datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")

# Instância global da API
api_instance = BTCIndicatorsAPI()

@app.route('/')
def home():
    return jsonify({
        "message": "🚀 BTC Indicators API está funcionando!",
        "status": "online",
        "version": "1.0.0",
        "endpoints": [
            "/api/indicators - Todos os indicadores analisados",
            "/api/summary - Resumo da análise",
            "/api/update - Força atualização",
            "/health - Status da API"
        ],
        "lastUpdate": api_instance.last_update
    })

@app.route('/api/indicators')
def get_indicators():
    """Retorna todos os indicadores analisados"""
    try:
        result = api_instance.analyze_indicators()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/summary')
def get_summary():
    """Retorna apenas o resumo da análise"""
    try:
        result = api_instance.analyze_indicators()
        return jsonify(result['summary'])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/update')
def force_update():
    """Força atualização dos dados"""
    try:
        result = api_instance.analyze_indicators()
        return jsonify({
            "message": "✅ Dados atualizados com sucesso!",
            "lastUpdate": result['summary']['lastUpdate'],
            "summary": result['summary']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check para monitoramento"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "lastUpdate": api_instance.last_update,
        "uptime": "API está rodando normalmente"
    })

def auto_update():
    """Atualização automática a cada 30 minutos"""
    while True:
        try:
            print(f"🔄 [{datetime.now()}] Executando atualização automática...")
            api_instance.analyze_indicators()
            print("✅ Atualização automática concluída!")
        except Exception as e:
            print(f"❌ Erro na atualização automática: {e}")
        
        # Aguarda 30 minutos (1800 segundos)
        time.sleep(1800)

if __name__ == '__main__':
    print("🚀 Iniciando BTC Indicators API...")
    print("📊 Carregando dados iniciais...")
    
    # Fazer uma análise inicial
    api_instance.analyze_indicators()
    
    # Iniciar thread de atualização automática
    print("⏰ Iniciando atualização automática (a cada 30 minutos)...")
    update_thread = threading.Thread(target=auto_update, daemon=True)
    update_thread.start()
    
    # Iniciar servidor
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Servidor iniciando na porta {port}...")
