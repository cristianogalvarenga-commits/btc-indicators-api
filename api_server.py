from flask import Flask, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import requests
import threading
import time
import logging

# Importar o scraper atualizado
from coinmarketcap_scraper_v2 import CoinMarketCapScraper

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class BTCIndicatorsAPI:
    def __init__(self):
        self.data_file = os.path.join(os.getcwd(), 'indicators_data.json')
        self.last_update = None
        self.indicators_data = {}
        self.scraper = CoinMarketCapScraper()
        self.load_data()
        
    def load_data(self):
        """Carrega dados do arquivo JSON ou inicializa com scraping"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.indicators_data = data.get('indicators', {})
                    self.last_update = data.get('last_update')
                logger.info("Dados carregados do arquivo JSON.")
            else:
                logger.info("Arquivo JSON não encontrado. Iniciando scraping inicial...")
                self.indicators_data = self.scraper.scrape_indicators()
                if self.indicators_data:
                    self.last_update = datetime.now().isoformat()
                    self.save_data()
                else:
                    logger.error("Falha ao coletar dados iniciais via scraping. Usando dados de fallback.")
                    self.indicators_data = self.scraper.get_fallback_data()
                    self.last_update = datetime.now().isoformat()
                    self.save_data()
        except Exception as e:
            logger.error(f"Erro ao carregar/inicializar dados: {e}. Usando dados de fallback.")
            self.indicators_data = self.scraper.get_fallback_data()
            self.last_update = datetime.now().isoformat()
            self.save_data()
    
    def calculate_proximity(self, current, reference, compare_type):
        """Calcula a proximidade ao topo"""
        if current is None or reference is None or reference == 0:
            return None
        
        try:
            if compare_type == ">=":
                if current >= reference:
                    return 100.0
                else:
                    return (current / reference) * 100
            elif compare_type == "<=": # Lógica inversa para dominância do BTC
                if current <= reference:
                    return 100.0
                else:
                    # Quanto mais próximo de 'reference' (por baixo), mais perto de 100%
                    max_dominance = 70.0 # Valor de dominância considerado alto
                    if current >= max_dominance: # Se estiver muito alto, longe do topo
                        return 0.0
                    elif current <= reference: # Se já atingiu ou passou o ponto de referência
                        return 100.0
                    else:
                        # Calcula a porcentagem de proximidade de forma inversa
                        return ((max_dominance - current) / (max_dominance - reference)) * 100
            else:
                return None
        except (ZeroDivisionError, TypeError):
            return None
    
    def analyze_indicators(self):
        """Análise completa de todos os indicadores"""
        logger.info(f"🚀 [{datetime.now()}] Iniciando análise dos indicadores BTC...")
        
        # Forçar atualização dos dados via scraping
        scraped_data = self.scraper.scrape_indicators()
        if scraped_data:
            self.indicators_data = scraped_data
            self.last_update = datetime.now().isoformat()
            self.save_data()
            logger.info("Dados atualizados via scraping.")
        else:
            logger.warning("Falha ao coletar dados via scraping. Usando dados existentes/fallback.")
            self.load_data()

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
        
        logger.info(f"✅ Análise concluída: {in_cycle_count}/{valid_count} na zona, média {average_proximity:.1f}%")
        
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
            logger.error(f"Erro ao salvar dados: {e}")

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
            logger.info(f"🔄 [{datetime.now()}] Executando atualização automática...")
            api_instance.analyze_indicators()
            logger.info("✅ Atualização automática concluída!")
        except Exception as e:
            logger.error(f"❌ Erro na atualização automática: {e}")
        
        # Aguarda 30 minutos (1800 segundos)
        time.sleep(1800)

if __name__ == '__main__':
    logger.info("🚀 Iniciando BTC Indicators API...")
    logger.info("📊 Carregando dados iniciais...")
    
    # Fazer uma análise inicial
    api_instance.analyze_indicators()
    
    # Iniciar thread de atualização automática
    logger.info("⏰ Iniciando atualização automática (a cada 30 minutos)...")
    update_thread = threading.Thread(target=auto_update, daemon=True)
    update_thread.start()
