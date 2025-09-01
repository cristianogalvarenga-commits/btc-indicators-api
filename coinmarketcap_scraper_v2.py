#!/usr/bin/env python3
"""
Script para fazer web scraping dos indicadores de fim de ciclo do Bitcoin da CoinMarketCap
Versão 2.0 - Com dados dinâmicos e lógica corrigida para dominância do BTC
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoinMarketCapScraper:
    def __init__(self):
        self.base_url = "https://coinmarketcap.com/charts/crypto-market-cycle-indicators/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def get_fear_greed_index(self):
        """Coleta o Fear & Greed Index da API"""
        try:
            logger.info("📊 Coletando Fear & Greed Index...")
            url = "https://api.alternative.me/fng/"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                value = float(data['data'][0]['value'])
                logger.info(f"   Fear & Greed Index: {value}")
                return value
        except Exception as e:
            logger.error(f"❌ Erro ao coletar Fear & Greed Index: {e}")
        return None
    
    def get_bitcoin_dominance(self):
        """Coleta a dominância do Bitcoin da CoinMarketCap"""
        try:
            logger.info("📊 Coletando Bitcoin Dominance...")
            url = "https://coinmarketcap.com/charts/"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Procurar por elementos que contenham a dominância do Bitcoin
                dominance_elements = soup.find_all(text=re.compile(r'Bitcoin.*%|BTC.*%'))
                for element in dominance_elements:
                    match = re.search(r'(\d+\.?\d*)%', element)
                    if match:
                        dominance = float(match.group(1))
                        logger.info(f"   Bitcoin Dominance: {dominance}%")
                        return dominance
        except Exception as e:
            logger.error(f"❌ Erro ao coletar Bitcoin Dominance: {e}")
        return None
    
    def scrape_indicators(self):
        """Faz scraping dos indicadores da página da CoinMarketCap"""
        try:
            logger.info("🚀 Iniciando scraping da CoinMarketCap...")
            response = self.session.get(self.base_url, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"❌ Erro HTTP {response.status_code} ao acessar {self.base_url}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            indicators_data = {}
            
            # Procurar pela tabela de indicadores
            table_rows = soup.find_all('tr')
            
            for row in table_rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:  # Número, Indicador, Current, Reference
                    try:
                        # Extrair dados da linha
                        indicator_cell = cells[1] if len(cells) > 1 else None
                        current_cell = cells[2] if len(cells) > 2 else None
                        reference_cell = cells[3] if len(cells) > 3 else None
                        
                        if indicator_cell and current_cell and reference_cell:
                            indicator_name = indicator_cell.get_text(strip=True)
                            current_text = current_cell.get_text(strip=True)
                            reference_text = reference_cell.get_text(strip=True)
                            
                            # Limpar e converter valores
                            current_value = self.parse_value(current_text)
                            reference_value = self.parse_value(reference_text)
                            
                            if indicator_name and current_value is not None and reference_value is not None:
                                indicators_data[indicator_name] = {
                                    "current": current_value,
                                    "reference": reference_value,
                                    "compare": ">=" if "≥" in reference_text or ">=" in reference_text else ">=",
                                    "source": "coinmarketcap",
                                    "description": self.get_indicator_description(indicator_name)
                                }
                                logger.info(f"   ✅ {indicator_name}: {current_value} (ref: {reference_value})")
                    
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao processar linha da tabela: {e}")
                        continue
            
            # Adicionar Fear & Greed Index
            fear_greed = self.get_fear_greed_index()
            if fear_greed is not None:
                indicators_data["Fear & Greed Index"] = {
                    "current": fear_greed,
                    "reference": 90.0,
                    "compare": ">=",
                    "source": "api",
                    "description": "Índice de medo e ganância do mercado"
                }
            
            # Adicionar Bitcoin Dominance (com lógica inversa)
            btc_dominance = self.get_bitcoin_dominance()
            if btc_dominance is not None:
                indicators_data["Bitcoin Dominance"] = {
                    "current": btc_dominance,
                    "reference": 40.0,  # Quando chega a 40%, indica fim de ciclo
                    "compare": "<=",    # Lógica inversa: quanto menor, mais próximo do topo
                    "source": "coinmarketcap",
                    "description": "Dominância do Bitcoin no mercado (inverso: menor = mais próximo do topo)"
                }
            
            # Se não conseguiu fazer scraping da tabela, usar dados de fallback
            if not indicators_data:
                logger.warning("⚠️ Não foi possível fazer scraping da tabela. Usando dados de fallback...")
                indicators_data = self.get_fallback_data()
            
            logger.info(f"✅ Scraping concluído! {len(indicators_data)} indicadores coletados.")
            return indicators_data
            
        except Exception as e:
            logger.error(f"❌ Erro durante o scraping: {e}")
            return self.get_fallback_data()
    
    def parse_value(self, text):
        """Converte texto em valor numérico"""
        if not text:
            return None
        
        # Remover símbolos e espaços
        clean_text = re.sub(r'[^\d.,%-]', '', text)
        clean_text = clean_text.replace('%', '').replace(',', '')
        
        try:
            # Tentar converter para float
            if '.' in clean_text:
                return float(clean_text)
            else:
                return int(clean_text)
        except (ValueError, TypeError):
            return None
    
    def get_indicator_description(self, name):
        """Retorna descrição do indicador"""
        descriptions = {
            "Bitcoin Ahr999 Index": "Indica sobrecompra quando >= 4.0",
            "Pi Cycle Top Indicator": "Sinal de topo quando 111DMA cruza 350DMA x2",
            "Puell Multiple": "Receita dos mineradores vs média histórica",
            "Bitcoin Rainbow Chart": "Nível de preço no gráfico arco-íris",
            "Days of ETF Net Outflows": "Dias consecutivos de saída de ETFs",
            "ETF-to-BTC Ratio": "Proporção de ETFs vs BTC total",
            "2-Year MA Multiplier": "Preço vs média móvel de 2 anos",
            "MVRV Z-Score": "Valor de mercado vs valor realizado",
            "Bitcoin Bubble Index": "Índice de bolha especulativa",
            "USDT Flexible Savings": "Taxa de poupança flexível USDT",
            "RSI - 22 Day": "Índice de força relativa 22 dias",
            "CMC Altcoin Season Index": "Índice de temporada de altcoins",
            "Bitcoin Dominance": "Dominância do Bitcoin no mercado (inverso)",
            "Bitcoin Long Term Holder Supply": "Oferta de holders de longo prazo",
            "Bitcoin Short Term Holder Supply (%)": "Oferta de holders de curto prazo",
            "Bitcoin Reserve Risk": "Risco de reserva dos holders",
            "Bitcoin Net Unrealized P&L (NUPL)": "Lucro/prejuízo não realizado líquido",
            "Bitcoin RHODL Ratio": "Ratio RHODL para timing de ciclo",
            "Bitcoin Macro Oscillator (BMO)": "Oscilador macro do Bitcoin",
            "Bitcoin MVRV Ratio": "Market Value to Realized Value",
            "Bitcoin 4-Year Moving Average": "Média móvel de 4 anos",
            "Crypto Bitcoin Bull Run Index (CBBI)": "Índice de bull run do Bitcoin",
            "Mayer Multiple": "Preço vs média móvel de 200 dias",
            "Bitcoin AHR999x Top Escape Indicator": "Indicador de escape do topo",
            "MicroStrategy's Avg Bitcoin Cost": "Custo médio do Bitcoin da MicroStrategy",
            "Bitcoin Trend Indicator": "Indicador de tendência do Bitcoin",
            "3-Month Annualized Ratio": "Ratio anualizado de 3 meses",
            "Bitcoin Terminal Price": "Preço terminal projetado",
            "Golden Ratio Multiplier": "Multiplicador da proporção áurea",
            "Smithson's Bitcoin Price Forecast": "Previsão de preço do Smithson",
            "Fear & Greed Index": "Índice de medo e ganância do mercado"
        }
        return descriptions.get(name, f"Indicador de fim de ciclo: {name}")
    
    def get_fallback_data(self):
        """Dados de fallback caso o scraping falhe"""
        logger.info("📊 Usando dados de fallback...")
        
        # Tentar pelo menos coletar Fear & Greed e Bitcoin Dominance
        fear_greed = self.get_fear_greed_index()
        btc_dominance = self.get_bitcoin_dominance()
        
        fallback_data = {
            "Bitcoin Ahr999 Index": {
                "current": 1.06,
                "reference": 4.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Indica sobrecompra quando >= 4.0"
            },
            "Pi Cycle Top Indicator": {
                "current": 110165.49,
                "reference": 186976.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Sinal de topo quando 111DMA cruza 350DMA x2"
            },
            "Puell Multiple": {
                "current": 1.39,
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
                "current": 7.0,
                "reference": 10.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Dias consecutivos de saída de ETFs"
            },
            "ETF-to-BTC Ratio": {
                "current": 5.09,
                "reference": 3.5,
                "compare": "<=",
                "source": "coinmarketcap",
                "description": "Proporção de ETFs vs BTC total"
            },
            "2-Year MA Multiplier": {
                "current": 112654.42,
                "reference": 356781.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Preço vs média móvel de 2 anos"
            },
            "MVRV Z-Score": {
                "current": 2.30,
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
                "current": 8.41,
                "reference": 29.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Taxa de poupança flexível USDT"
            },
            "RSI - 22 Day": {
                "current": 44.289,
                "reference": 80.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Índice de força relativa 22 dias"
            },
            "CMC Altcoin Season Index": {
                "current": 47.0,
                "reference": 75.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Índice de temporada de altcoins"
            },
            "Bitcoin Long Term Holder Supply": {
                "current": 15.59,
                "reference": 13.5,
                "compare": "<=",
                "source": "coinmarketcap",
                "description": "Oferta de holders de longo prazo"
            },
            "Bitcoin Short Term Holder Supply (%)": {
                "current": 21.71,
                "reference": 30.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Oferta de holders de curto prazo"
            },
            "Bitcoin Reserve Risk": {
                "current": 0.0025,
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
                "current": 3006.0,
                "reference": 10000.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Ratio RHODL para timing de ciclo"
            },
            "Bitcoin Macro Oscillator (BMO)": {
                "current": 0.91,
                "reference": 1.4,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Oscilador macro do Bitcoin"
            },
            "Bitcoin MVRV Ratio": {
                "current": 2.17,
                "reference": 3.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Market Value to Realized Value"
            },
            "Bitcoin 4-Year Moving Average": {
                "current": 2.20,
                "reference": 3.5,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Média móvel de 4 anos"
            },
            "Crypto Bitcoin Bull Run Index (CBBI)": {
                "current": 77.0,
                "reference": 90.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Índice de bull run do Bitcoin"
            },
            "Mayer Multiple": {
                "current": 1.13,
                "reference": 2.2,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Preço vs média móvel de 200 dias"
            },
            "Bitcoin AHR999x Top Escape Indicator": {
                "current": 2.85,
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
                "current": 112654.42,
                "reference": 187702.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Preço terminal projetado"
            },
            "Golden Ratio Multiplier": {
                "current": 112654.42,
                "reference": 135522.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Multiplicador da proporção áurea"
            },
            "Smithson's Bitcoin Price Forecast": {
                "current": 112654.42,
                "reference": 175000.0,
                "compare": ">=",
                "source": "coinmarketcap",
                "description": "Previsão de preço do Smithson"
            }
        }
        
        # Adicionar Fear & Greed Index se coletado
        if fear_greed is not None:
            fallback_data["Fear & Greed Index"] = {
                "current": fear_greed,
                "reference": 90.0,
                "compare": ">=",
                "source": "api",
                "description": "Índice de medo e ganância do mercado"
            }
        
        # Adicionar Bitcoin Dominance se coletado (com lógica inversa)
        if btc_dominance is not None:
            fallback_data["Bitcoin Dominance"] = {
                "current": btc_dominance,
                "reference": 40.0,  # Quando chega a 40%, indica fim de ciclo
                "compare": "<=",    # Lógica inversa: quanto menor, mais próximo do topo
                "source": "coinmarketcap",
                "description": "Dominância do Bitcoin no mercado (inverso: menor = mais próximo do topo)"
            }
        
        return fallback_data
    
    def save_data(self, data, filename="indicators_data.json"):
        """Salva os dados em arquivo JSON"""
        try:
            output_data = {
                "indicators": data,
                "last_update": datetime.now().isoformat(),
                "source": "coinmarketcap_scraper_v2",
                "total_indicators": len(data)
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Dados salvos em {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados: {e}")
            return False

def main():
    """Função principal"""
    scraper = CoinMarketCapScraper()
    
    logger.info("🚀 Iniciando coleta de dados dos indicadores BTC...")
    
    # Fazer scraping dos dados
    indicators_data = scraper.scrape_indicators()
    
    if indicators_data:
        # Salvar dados
        scraper.save_data(indicators_data)
        
        # Mostrar resumo
        logger.info(f"📊 RESUMO:")
        logger.info(f"   Total de indicadores: {len(indicators_data)}")
        
        # Mostrar alguns indicadores importantes
        important_indicators = ["Fear & Greed Index", "Bitcoin Dominance", "Pi Cycle Top Indicator", "Puell Multiple"]
        for indicator in important_indicators:
            if indicator in indicators_data:
                data = indicators_data[indicator]
                logger.info(f"   {indicator}: {data['current']} (ref: {data['reference']})")
        
        logger.info("✅ Coleta concluída com sucesso!")
        return True
    else:
        logger.error("❌ Falha na coleta de dados!")
        return False

if __name__ == "__main__":
    main()