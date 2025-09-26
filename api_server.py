"""
API Server Bitcoin Market Cycle - Versão de Teste
Dados simulados realistas para testar o frontend
"""

from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import pytz
import threading
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Dados simulados realistas baseados em valores típicos do mercado
SIMULATED_DATA = {
    "Bitcoin Ahr999 Index": {
        "current": 0.98,
        "reference": 4.0,
        "description": "Índice que combina preço e média móvel de 200 dias. Valores acima de 4 indicam possível topo de mercado.",
        "unit": ""
    },
    "Pi Cycle Top Indicator": {
        "current": 111351.78,
        "reference": 190771,
        "description": "Cruzamento de médias móveis de 111 e 350 dias. Quando a 111DMA cruza a 350DMA x2, indica possível topo.",
        "unit": "$"
    },
    "Puell Multiple": {
        "current": 1.13,
        "reference": 2.2,
        "description": "Receita diária dos mineradores vs média de 365 dias. Valores acima de 2.2 sugerem fim de ciclo.",
        "unit": ""
    },
    "Bitcoin Rainbow Chart": {
        "current": 3,
        "reference": 5,
        "description": "Gráfico logarítmico com bandas de preço. Banda 5 (vermelha) indica possível topo de mercado.",
        "unit": ""
    },
    "2-Year MA Multiplier": {
        "current": 111312.05,
        "reference": 364280,
        "description": "Multiplicador da média móvel de 2 anos. Valores próximos a $364k indicam topo histórico.",
        "unit": "$"
    },
    "MVRV Z-Score": {
        "current": 2.12,
        "reference": 5.0,
        "description": "Z-Score do MVRV (Market Value to Realized Value). Valores acima de 5 indicam possível topo.",
        "unit": ""
    },
    "Bitcoin Bubble Index": {
        "current": 13.48,
        "reference": 80,
        "description": "Índice de bolha baseado em desvios de preço. Valores acima de 80 indicam bolha extrema.",
        "unit": ""
    },
    "Bitcoin Dominance": {
        "current": 57.8,
        "reference": 40,
        "description": "Dominância do Bitcoin no mercado cripto. Quando cai para 40%, indica possível fim de ciclo.",
        "unit": "%"
    },
    "Bitcoin MVRV Ratio": {
        "current": 2.10,
        "reference": 3.0,
        "description": "Market Value to Realized Value Ratio. Valores acima de 3 indicam sobrevalorização.",
        "unit": ""
    },
    "Mayer Multiple": {
        "current": 1.13,
        "reference": 2.2,
        "description": "Preço atual vs média móvel de 200 dias. Valores acima de 2.2 indicam sobrevalorização.",
        "unit": ""
    },
    "Fear & Greed Index": {
        "current": 55,
        "reference": 80,
        "description": "Índice de medo e ganância do mercado. Valores acima de 80 indicam ganância extrema.",
        "unit": ""
    },
    "Bitcoin Net Unrealized P&L": {
        "current": 54.91,
        "reference": 70,
        "description": "P&L não realizado líquido (NUPL). Valores acima de 70% indicam euforia extrema.",
        "unit": "%"
    },
    "Bitcoin RHODL Ratio": {
        "current": 2754,
        "reference": 10000,
        "description": "Ratio RHODL (Realized HODL). Valores acima de 10000 indicam possível topo.",
        "unit": ""
    },
    "Bitcoin Macro Oscillator": {
        "current": 0.84,
        "reference": 1.4,
        "description": "Oscilador macro baseado em ciclos. Valores acima de 1.4 indicam fim de ciclo.",
        "unit": ""
    },
    "Bitcoin 4-Year Moving Average": {
        "current": 2.13,
        "reference": 3.5,
        "description": "Média móvel de 4 anos. Valores acima de 3.5 indicam possível topo de ciclo.",
        "unit": ""
    },
    "Crypto Bitcoin Bull Run Index": {
        "current": 74,
        "reference": 90,
        "description": "Índice de bull run cripto (CBBI). Valores acima de 90 indicam fim de bull run.",
        "unit": ""
    },
    "Bitcoin Reserve Risk": {
        "current": 0.0024,
        "reference": 0.005,
        "description": "Risco de reserva baseado em HODL waves. Valores acima de 0.005 indicam alto risco.",
        "unit": ""
    },
    "Golden Ratio Multiplier": {
        "current": 112035.99,
        "reference": 135522,
        "description": "Multiplicador da proporção áurea. Valores próximos a $135k indicam resistência forte.",
        "unit": "$"
    },
    "Bitcoin Terminal Price": {
        "current": 112035.99,
        "reference": 187702,
        "description": "Preço terminal baseado em modelos. Valores próximos a $187k indicam topo teórico.",
        "unit": "$"
    },
    "Smithson Bitcoin Price Forecast": {
        "current": 112035.99,
        "reference": 175000,
        "description": "Previsão de preço Smithson. Modelo baseado em análise técnica e fundamentalista.",
        "unit": "$"
    },
    "Bitcoin Long Term Holder Supply": {
        "current": 15.47,
        "reference": 13.5,
        "description": "Suprimento de holders de longo prazo. Valores abaixo de 13.5M indicam distribuição.",
        "unit": "M"
    },
    "Bitcoin Short Term Holder Supply": {
        "current": 22.31,
        "reference": 30,
        "description": "Suprimento de holders de curto prazo (%). Valores acima de 30% indicam especulação.",
        "unit": "%"
    },
    "Bitcoin AHR999x Top Escape": {
        "current": 3.04,
        "reference": 0.45,
        "description": "Indicador de escape do topo AHR999x. Valores abaixo de 0.45 indicam momento de venda.",
        "unit": ""
    },
    "MicroStrategy Avg Bitcoin Cost": {
        "current": 73526,
        "reference": 155655,
        "description": "Custo médio do Bitcoin da MicroStrategy. Referência baseada em compras históricas.",
        "unit": "$"
    },
    "Bitcoin Trend Indicator": {
        "current": 6.14,
        "reference": 7,
        "description": "Indicador de tendência baseado em momentum. Valores acima de 7 indicam possível reversão.",
        "unit": ""
    },
    "3-Month Annualized Ratio": {
        "current": 9.95,
        "reference": 30,
        "description": "Ratio anualizado de 3 meses. Valores acima de 30% indicam crescimento insustentável.",
        "unit": "%"
    },
    "Days of ETF Net Outflows": {
        "current": 2,
        "reference": 10,
        "description": "Dias consecutivos de saídas líquidas de ETFs. Mais de 10 dias pode indicar fim de ciclo.",
        "unit": " dias"
    },
    "ETF-to-BTC Ratio": {
        "current": 3.2,
        "reference": 3.5,
        "description": "Proporção entre ETFs e Bitcoin. Valores abaixo de 3.5% podem indicar fim de ciclo.",
        "unit": "%"
    },
    "USDT Flexible Savings": {
        "current": 5.66,
        "reference": 29,
        "description": "Taxa de poupança flexível USDT. Taxas acima de 29% indicam alta demanda por stablecoins.",
        "unit": "%"
    },
    "RSI - 22 Day": {
        "current": 47.173,
        "reference": 80,
        "description": "Índice de Força Relativa de 22 dias. Valores acima de 80 indicam sobrecompra extrema.",
        "unit": ""
    },
    "CMC Altcoin Season Index": {
        "current": 54,
        "reference": 75,
        "description": "Índice de temporada de altcoins. Valores acima de 75 indicam altseason extrema.",
        "unit": ""
    }
}

def calculate_proximity(indicator_name, current, reference):
    """Calcula proximidade ao fim de ciclo (0-100%)"""
    if current is None or reference is None or reference == 0:
        return 0
    
    inverse_indicators = [
        "Bitcoin Dominance", 
        "Bitcoin Long Term Holder Supply", 
        "Bitcoin AHR999x Top Escape",
        "ETF-to-BTC Ratio"
    ]
    
    if indicator_name in inverse_indicators:
        proximity = ((reference - current) / reference) * 100
        proximity = max(0, proximity)
    else:
        proximity = (current / reference) * 100
    
    return min(100, max(0, proximity))

def is_in_risk_zone(indicator_name, current, reference):
    """Determina se o indicador está na zona de risco"""
    if current is None or reference is None:
        return False
    
    inverse_indicators = [
        "Bitcoin Dominance", 
        "Bitcoin Long Term Holder Supply", 
        "Bitcoin AHR999x Top Escape",
        "ETF-to-BTC Ratio"
    ]
    
    if indicator_name in inverse_indicators:
        return current <= reference
    else:
        return current >= reference

def get_risk_level(proximity):
    """Determina nível de risco baseado na proximidade"""
    if proximity >= 90:
        return "CRÍTICO"
    elif proximity >= 70:
        return "ALTO"
    elif proximity >= 50:
        return "MÉDIO"
    else:
        return "BAIXO"

def process_indicators():
    """Processa todos os indicadores e calcula métricas"""
    indicators = {}
    total_proximity = 0
    valid_count = 0
    in_risk_zone_count = 0
    risk_distribution = {"BAIXO": 0, "MÉDIO": 0, "ALTO": 0, "CRÍTICO": 0}
    
    for name, data in SIMULATED_DATA.items():
        current = data["current"]
        reference = data["reference"]
        
        proximity = calculate_proximity(name, current, reference)
        in_risk = is_in_risk_zone(name, current, reference)
        risk_level = get_risk_level(proximity)
        
        indicators[name] = {
            "current": current,
            "reference": reference,
            "proximity": round(proximity, 1),
            "in_risk_zone": in_risk,
            "risk_level": risk_level,
            "description": data["description"],
            "unit": data["unit"]
        }
        
        total_proximity += proximity
        valid_count += 1
        
        if in_risk:
            in_risk_zone_count += 1
        
        risk_distribution[risk_level] += 1
    
    avg_proximity = total_proximity / valid_count if valid_count > 0 else 0
    risk_zone_percentage = (in_risk_zone_count / valid_count) * 100 if valid_count > 0 else 0
    
    if avg_proximity >= 80:
        status = "🔴 ALTO RISCO - Possível fim de ciclo"
    elif avg_proximity >= 60:
        status = "🟡 MÉDIO RISCO - Monitorar de perto"
    elif avg_proximity >= 40:
        status = "🟠 BAIXO-MÉDIO RISCO - Meio do ciclo"
    else:
        status = "🟢 BAIXO RISCO - Início do ciclo"
    
    summary = {
        "total_indicators": valid_count,
        "in_risk_zone": in_risk_zone_count,
        "avg_proximity": round(avg_proximity, 1),
        "risk_zone_percentage": round(risk_zone_percentage, 1),
        "general_status": status,
        "risk_distribution": risk_distribution,
        "last_update": datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()
    }
    
    return indicators, summary

@app.route('/')
def home():
    return jsonify({
        "message": "🚀 Bitcoin Market Cycle API - Versão de Teste",
        "status": "online",
        "version": "TEST-1.0.0",
        "last_update": datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat(),
        "data_source": "Dados Simulados Realistas",
        "total_indicators": len(SIMULATED_DATA),
        "note": "Esta é uma versão de teste com dados simulados para validar o frontend"
    })

@app.route('/api/indicators')
def get_indicators():
    indicators, summary = process_indicators()
    return jsonify({
        "indicators": indicators,
        "last_update": datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()
    })

@app.route('/api/summary')
def get_summary():
    indicators, summary = process_indicators()
    return jsonify({
        "summary": summary,
        "last_update": datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()
    })

@app.route('/api/update')
def force_update():
    indicators, summary = process_indicators()
    return jsonify({
        "message": "✅ Dados atualizados com sucesso!",
        "timestamp": datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat(),
        "total_indicators": len(indicators),
        "avg_proximity": summary['avg_proximity'],
        "in_risk_zone": summary['in_risk_zone'],
        "risk_zone_percentage": summary['risk_zone_percentage'],
        "note": "Dados simulados para teste"
    })

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "last_update": datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat(),
        "indicators_count": len(SIMULATED_DATA),
        "version": "TEST-1.0.0",
        "data_source": "Simulated Data"
    })

if __name__ == '__main__':
    print("🚀 Iniciando Bitcoin Market Cycle API - Versão de Teste")
    print(f"📊 {len(SIMULATED_DATA)} indicadores simulados carregados")
    
    indicators, summary = process_indicators()
    print(f"✅ Proximidade média: {summary['avg_proximity']:.1f}%")
    print(f"🔴 Na zona de risco: {summary['in_risk_zone']}/{summary['total_indicators']}")
    
    app.run(host='0.0.0.0', port=5002, debug=False)
