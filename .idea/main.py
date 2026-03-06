import flet as ft
import threading
import random
import datetime
import requests
import xml.etree.ElementTree as ET
import yfinance as yf
import feedparser
import time

# ----------------------------------------------------------------------
# ЗАГЛУШКИ
# ----------------------------------------------------------------------
def get_economic_news_mock():
    return [
        {"Date": "10:30", "Title": "ФРС сохранила ставку на уровне 5.5% (демо)", "Link": "#"},
        {"Date": "09:45", "Title": "Нефть Brent выросла до $85 за баррель (демо)", "Link": "#"},
        {"Date": "Вчера", "Title": "Инфляция в США замедлилась до 3.2% (демо)", "Link": "#"},
        {"Date": "Вчера", "Title": "Китай снижает пошлины на импорт (демо)", "Link": "#"},
        {"Date": "2 дня назад", "Title": "Apple представила новые MacBook (демо)", "Link": "#"},
    ]

def get_stock_quote_mock(ticker):
    change = round(random.uniform(-3.5, 5.2), 2)
    change_str = f"{change:+.2f}%"
    price = round(random.uniform(50, 500), 2)
    quote_data = {
        "Company": f"Company {ticker.upper()} (демо)",
        "Price": f"${price}",
        "Change": change_str,
        "Volume": f"{random.randint(1, 50)}M",
        "P/E": str(round(random.uniform(10, 30), 1)),
        "Market Cap": f"${random.randint(10, 1000)}B",
    }
    news_items = [
        {"Title": f"{ticker} announces new product (demo)", "Link": "#", "Date": "1 hour ago"},
        {"Title": f"Analysts upgrade {ticker} (demo)", "Link": "#", "Date": "3 hours ago"},
        {"Title": f"{ticker} earnings beat expectations (demo)", "Link": "#", "Date": "yesterday"},
    ]
    return quote_data, news_items

def screen_stocks_mock():
    tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "AMD", "META", "GOOGL"]
    stocks = []
    for t in tickers:
        change = round(random.uniform(-10.0, 10.0), 2)
        sign = "+" if change >= 0 else ""
        stocks.append({
            "Ticker": t,
            "Company": f"{t} Inc. (demo)",
            "Price": f"${round(random.uniform(50, 900), 2)}",
            "Change": f"{sign}{change}%",
        })
    return stocks

def get_forecast_data_mock():
    return [
        {"ticker": "AAPL", "company": "Apple (demo)", "target": "$210", "change": "+2.3%", "recommendation": "BUY"},
        {"ticker": "TSLA", "company": "Tesla (demo)", "target": "$280", "change": "-1.2%", "recommendation": "HOLD"},
        {"ticker": "MSFT", "company": "Microsoft (demo)", "target": "$450", "change": "+3.1%", "recommendation": "BUY"},
        {"ticker": "NVDA", "company": "NVIDIA (demo)", "target": "$950", "change": "+5.7%", "recommendation": "STRONG BUY"},
    ]

def get_currency_rates_mock():
    return [
        {"pair": "USD/RUB", "rate": 92.35, "change": "+0.45"},
        {"pair": "EUR/RUB", "rate": 100.12, "change": "-0.20"},
        {"pair": "CNY/RUB", "rate": 12.75, "change": "+0.03"},
        {"pair": "GBP/RUB", "rate": 117.80, "change": "+0.15"},
    ]

# ----------------------------------------------------------------------
# РЕАЛЬНЫЕ ФУНКЦИИ
# ----------------------------------------------------------------------

def get_stock_quote_real(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or 'regularMarketPrice' not in info:
            print(f"DEBUG: {ticker} - no price data")
            return None, None

        quote_data = {
            "Company": info.get('longName', info.get('shortName', ticker.upper())),
            "Price": f"${info.get('regularMarketPrice', 0):.2f}",
            "Change": f"{info.get('regularMarketChangePercent', 0):+.2f}%",
            "Volume": f"{info.get('volume', 0):,}",
            "P/E": f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else 'N/A',
            "Market Cap": f"${info.get('marketCap', 0)/1e9:.2f}B" if info.get('marketCap') else 'N/A',
        }
        news_items = []
        if hasattr(stock, 'news') and stock.news:
            for item in stock.news[:3]:
                news_items.append({
                    "Title": item.get('title', ''),
                    "Link": item.get('link', '#'),
                    "Date": "Just now",
                })
        return quote_data, news_items
    except Exception as e:
        print(f"yfinance quote error for {ticker}: {e}")
        return None, None

def get_forecast_data_real():
    if hasattr(get_forecast_data_real, "cache"):
        cache_time, cache_data = get_forecast_data_real.cache
        if time.time() - cache_time < 300:
            return cache_data

    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    forecast = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            target = info.get('targetMeanPrice', 'N/A')
            if target != 'N/A':
                target = f"${target:.2f}"
            rec = info.get('recommendationKey', 'hold').upper()
            price = info.get('regularMarketPrice', 0)
            prev_close = info.get('regularMarketPreviousClose', price)
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
            company = info.get('shortName', ticker)[:15]

            forecast.append({
                "ticker": ticker,
                "company": company,
                "target": target,
                "change": f"{change_pct:+.2f}%",
                "recommendation": rec,
            })
        except Exception as e:
            print(f"Forecast error for {ticker}: {e}")
            continue

    result = forecast if forecast else None
    if result:
        get_forecast_data_real.cache = (time.time(), result)
    return result

def screen_stocks_real():
    if hasattr(screen_stocks_real, "cache"):
        cache_time, cache_data = screen_stocks_real.cache
        if time.time() - cache_time < 300:
            print(f"DEBUG: Using cached screener data ({len(cache_data)} items)")
            return cache_data

    # Расширенный список тикеров (топ-50 по капитализации)
    tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "BRK-B", "JPM", "V",
        "JNJ", "WMT", "PG", "UNH", "HD", "DIS", "MA", "PYPL", "NFLX", "ADBE",
        "CMCSA", "PFE", "TMO", "CRM", "NKE", "ABT", "ABBV", "CVX", "KO", "PEP",
        "MRK", "WFC", "INTC", "AMD", "T", "QCOM", "COST", "DHR", "NEE", "MCD",
        "TXN", "HON", "LOW", "LIN", "UPS", "SBUX", "BA", "CAT", "AMGN", "IBM"
    ]
    stocks = []
    print("DEBUG: Starting screener fetch...")
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get('regularMarketPrice', 0)
            change = info.get('regularMarketChangePercent', 0)
            if price and change:
                print(f"DEBUG: {ticker} - price: {price:.2f}, change: {change:.2f}%")
                # Условие: изменение по модулю больше 3%
                if abs(change) > 3:
                    sign = "+" if change >= 0 else ""
                    stocks.append({
                        "Ticker": ticker,
                        "Company": info.get('shortName', ticker)[:20],
                        "Price": f"${price:.2f}",
                        "Change": f"{sign}{change:.2f}%",
                    })
            else:
                print(f"DEBUG: {ticker} - no price/change data")
        except Exception as e:
            print(f"DEBUG: {ticker} - error: {e}")
            continue

    # Сортировка по абсолютному значению изменения (самые сильные движения сверху)
    stocks.sort(key=lambda x: abs(float(x['Change'].rstrip('%'))), reverse=True)
    result = stocks[:10] if stocks else None
    print(f"DEBUG: Screener found {len(stocks) if stocks else 0} real stocks with |change| > 3%")
    if result:
        screen_stocks_real.cache = (time.time(), result)
    return result

def get_currency_rates_real():
    try:
        today = datetime.datetime.now()
        today_str = today.strftime("%d/%m/%Y")
        yesterday = today - datetime.timedelta(days=1)
        yesterday_str = yesterday.strftime("%d/%m/%Y")

        url = "https://www.cbr.ru/scripts/XML_daily.asp"

        def fetch_rates(date_str):
            params = {'date_req': date_str}
            resp = requests.get(url, params=params, timeout=10)
            root = ET.fromstring(resp.content)
            rates = {}
            for valute in root.findall('Valute'):
                char_code = valute.find('CharCode').text
                if char_code in ['USD', 'EUR', 'GBP', 'CNY', 'JPY']:
                    nominal = int(valute.find('Nominal').text)
                    value = float(valute.find('Value').text.replace(',', '.'))
                    rates[char_code] = value / nominal
            return rates

        today_rates = fetch_rates(today_str)
        yesterday_rates = fetch_rates(yesterday_str)

        if not yesterday_rates:
            yesterday2 = today - datetime.timedelta(days=2)
            yesterday2_str = yesterday2.strftime("%d/%m/%Y")
            yesterday_rates = fetch_rates(yesterday2_str)

        currency_map = {
            'USD': 'Доллар США',
            'EUR': 'Евро',
            'GBP': 'Фунт стерлингов',
            'CNY': 'Китайский юань',
            'JPY': 'Японская иена'
        }

        rates_list = []
        for code, name in currency_map.items():
            if code in today_rates:
                rate_today = today_rates[code]
                rate_yest = yesterday_rates.get(code, rate_today)
                change = rate_today - rate_yest
                change_str = f"{change:+.2f}"
                rates_list.append({
                    "pair": f"{code}/RUB",
                    "rate": round(rate_today, 2),
                    "change": change_str,
                })
        return rates_list if rates_list else None
    except Exception as e:
        print(f"Currency real error: {e}")
        return None

def get_economic_news_real():
    try:
        feed_url = "https://finance.yahoo.com/news/rssindex"
        feed = feedparser.parse(feed_url)
        entries = feed.entries[:7]
        news = []
        for entry in entries:
            published = entry.get('published', entry.get('updated', ''))
            date_str = published[:16] if published else "N/A"
            news.append({
                "Date": date_str,
                "Title": entry.get('title', ''),
                "Link": entry.get('link', '#'),
            })
        return news if news else None
    except Exception as e:
        print(f"RSS error: {e}")
        return None

# ----------------------------------------------------------------------
# УНИВЕРСАЛЬНАЯ ОБЁРТКА
# ----------------------------------------------------------------------
def safe_get(real_func, mock_func, *args, **kwargs):
    try:
        result = real_func(*args, **kwargs)
        if result is None or (isinstance(result, list) and len(result) == 0):
            print(f"Using mock for {real_func.__name__} (no real data)")
            return mock_func(*args, **kwargs) if callable(mock_func) else mock_func
        return result
    except Exception as e:
        print(f"Error in {real_func.__name__}, using mock: {e}")
        return mock_func(*args, **kwargs) if callable(mock_func) else mock_func

# ----------------------------------------------------------------------
# ОСНОВНОЕ ПРИЛОЖЕНИЕ
# ----------------------------------------------------------------------
def main(page: ft.Page):
    page.title = "Trader‘s Helper"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window_width = 800
    page.window_height = 900
    page.scroll = ft.ScrollMode.AUTO

    news_items = safe_get(get_economic_news_real, get_economic_news_mock)
    currency_data = safe_get(get_currency_rates_real, get_currency_rates_mock)
    screened_stocks = None
    forecast_data = None
    quote_data = {}
    stock_news = []

    page_title = ft.Text("📈 Trader‘s Helper", size=32, weight=ft.FontWeight.BOLD)

    ticker_input = ft.TextField(
        label="Введите тикер (например, AAPL, TSLA)",
        width=300,
        on_submit=lambda e: load_quote()
    )
    load_button = ft.Button("Загрузить котировку", on_click=lambda e: load_quote())

    quote_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Введите тикер для загрузки данных", italic=True)
            ]),
            padding=15,
            width=400
        )
    )

    nav_row = ft.Row([
        ft.Button("🏠 Главная", on_click=lambda _: change_tab(0)),
        ft.Button("📊 Скринер", on_click=lambda _: load_screener_and_show(1)),
        ft.Button("📈 Прогноз", on_click=lambda _: load_forecast_and_show(2)),
        ft.Button("💱 Валюты", on_click=lambda _: change_tab(3)),
    ], alignment=ft.MainAxisAlignment.CENTER)

    content_area = ft.Container(expand=True, padding=10)

    def load_screener_and_show(index):
        nonlocal screened_stocks
        content_area.content = ft.Column([
            ft.Text("Загрузка скринера... (это может занять 10-15 секунд)", size=16),
            ft.ProgressRing()
        ])
        page.update()

        def fetch():
            nonlocal screened_stocks
            screened_stocks = safe_get(screen_stocks_real, screen_stocks_mock)
            page.run_thread(lambda: change_tab(index))
        threading.Thread(target=fetch, daemon=True).start()

    def load_forecast_and_show(index):
        nonlocal forecast_data
        content_area.content = ft.Column([
            ft.Text("Загрузка прогноза...", size=16),
            ft.ProgressRing()
        ])
        page.update()

        def fetch():
            nonlocal forecast_data
            forecast_data = safe_get(get_forecast_data_real, get_forecast_data_mock)
            page.run_thread(lambda: change_tab(index))
        threading.Thread(target=fetch, daemon=True).start()

    def change_tab(index):
        content_area.content = get_content_for_index(index)
        page.update()

    def get_content_for_index(index):
        if index == 0:
            return ft.Column([
                ft.Text("🌍 Экономические новости мира", size=20, weight=ft.FontWeight.BOLD),
                ft.ListView(
                    controls=[
                        ft.ListTile(
                            title=ft.Text(n['Title']),
                            subtitle=ft.Text(n.get('Date', 'Just now')),
                            on_click=lambda _, url=n['Link']: page.launch_url(url)
                        ) for n in news_items
                    ],
                    height=400
                )
            ])
        elif index == 1:
            if screened_stocks is None:
                return ft.Text("Нажмите кнопку Скринер для загрузки данных.")
            if not screened_stocks:
                return ft.Text("Нет данных для отображения (используются заглушки).")
            return ft.Column([
                ft.Text("📈 Акции с движением >3% (вверх/вниз)", size=20, weight=ft.FontWeight.BOLD),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Ticker")),
                        ft.DataColumn(ft.Text("Company")),
                        ft.DataColumn(ft.Text("Price")),
                        ft.DataColumn(ft.Text("Change")),
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(s['Ticker'])),
                                ft.DataCell(ft.Text(s['Company'][:15])),
                                ft.DataCell(ft.Text(s['Price'])),
                                ft.DataCell(ft.Text(
                                    s['Change'],
                                    color="green" if s['Change'].startswith('+') else "red"
                                )),
                            ]
                        ) for s in screened_stocks
                    ]
                )
            ])
        elif index == 2:
            if forecast_data is None:
                return ft.Text("Нажмите кнопку Прогноз для загрузки данных.")
            if not forecast_data:
                return ft.Text("Нет данных для прогноза.")
            return ft.Column([
                ft.Text("📊 Прогноз по акциям", size=20, weight=ft.FontWeight.BOLD),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Ticker")),
                        ft.DataColumn(ft.Text("Company")),
                        ft.DataColumn(ft.Text("Target")),
                        ft.DataColumn(ft.Text("Change")),
                        ft.DataColumn(ft.Text("Rec.")),
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(f['ticker'])),
                                ft.DataCell(ft.Text(f['company'])),
                                ft.DataCell(ft.Text(f['target'])),
                                ft.DataCell(ft.Text(f['change'], color="green" if '+' in f['change'] else "red")),
                                ft.DataCell(ft.Text(f['recommendation'])),
                            ]
                        ) for f in forecast_data
                    ]
                ),
                ft.Text("⏱ Обновлено: " + datetime.datetime.now().strftime("%H:%M:%S"), size=12, italic=True),
                ft.Button("🔄 Обновить прогноз", on_click=lambda _: refresh_forecast()),
            ])
        else:
            if not currency_data:
                return ft.Text("Нет данных по валютам.")
            return ft.Column([
                ft.Text("💱 Курсы валют (ЦБ РФ)", size=20, weight=ft.FontWeight.BOLD),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Пара")),
                        ft.DataColumn(ft.Text("Курс")),
                        ft.DataColumn(ft.Text("Измен.")),
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(c['pair'])),
                                ft.DataCell(ft.Text(str(c['rate']))),
                                ft.DataCell(ft.Text(
                                    c['change'],
                                    color="green" if c['change'].startswith('+') else "red"
                                )),
                            ]
                        ) for c in currency_data
                    ]
                ),
                ft.Text("⏱ Обновлено: " + datetime.datetime.now().strftime("%H:%M:%S"), size=12, italic=True),
                ft.Button("🔄 Обновить курсы", on_click=lambda _: refresh_currencies()),
            ])

    def refresh_forecast():
        nonlocal forecast_data
        if hasattr(get_forecast_data_real, "cache"):
            delattr(get_forecast_data_real, "cache")
        forecast_data = safe_get(get_forecast_data_real, get_forecast_data_mock)
        change_tab(2)

    def refresh_currencies():
        nonlocal currency_data
        currency_data = safe_get(get_currency_rates_real, get_currency_rates_mock)
        change_tab(3)

    def load_quote():
        nonlocal quote_data, stock_news
        ticker = ticker_input.value
        if not ticker:
            return
        quote_card.content = ft.Container(content=ft.Text("Загрузка..."), padding=15)
        page.update()

        def fetch():
            nonlocal quote_data, stock_news
            q_data, s_news = get_stock_quote_real(ticker)
            if q_data:
                quote_data = q_data
                stock_news = s_news
                new_content = ft.Container(
                    content=ft.Column([
                        ft.Text(f"{quote_data.get('Company', ticker)}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.Text(f"Price: {quote_data.get('Price', 'N/A')}", size=16),
                            ft.Text(f"Change: {quote_data.get('Change', 'N/A')}",
                                   color="green" if '+' in str(quote_data.get('Change', '')) else "red"),
                        ]),
                        ft.Row([
                            ft.Text(f"Volume: {quote_data.get('Volume', 'N/A')}"),
                            ft.Text(f"P/E: {quote_data.get('P/E', 'N/A')}"),
                        ]),
                        ft.Text(f"Market Cap: {quote_data.get('Market Cap', 'N/A')}"),
                        ft.Divider(),
                        ft.Text("Последние новости:", weight=ft.FontWeight.BOLD),
                        ft.Column([
                            ft.TextButton(n['Title'], on_click=lambda _, url=n['Link']: page.launch_url(url))
                            for n in stock_news
                        ]) if stock_news else ft.Text("Нет новостей по акции.")
                    ]),
                    padding=15
                )
            else:
                q_mock, s_mock = get_stock_quote_mock(ticker)
                new_content = ft.Container(
                    content=ft.Column([
                        ft.Text(f"{q_mock.get('Company', ticker)} (демо)", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.Text(f"Price: {q_mock.get('Price', 'N/A')}", size=16),
                            ft.Text(f"Change: {q_mock.get('Change', 'N/A')}",
                                   color="green" if '+' in str(q_mock.get('Change', '')) else "red"),
                        ]),
                        ft.Row([
                            ft.Text(f"Volume: {q_mock.get('Volume', 'N/A')}"),
                            ft.Text(f"P/E: {q_mock.get('P/E', 'N/A')}"),
                        ]),
                        ft.Text(f"Market Cap: {q_mock.get('Market Cap', 'N/A')}"),
                        ft.Divider(),
                        ft.Text("Демо-новости (реальные не загрузились):", weight=ft.FontWeight.BOLD),
                        ft.Column([
                            ft.TextButton(n['Title'], on_click=lambda _, url=n['Link']: page.launch_url(url))
                            for n in s_mock
                        ])
                    ]),
                    padding=15
                )
            page.run_thread(lambda: set_quote_card(new_content))

        threading.Thread(target=fetch, daemon=True).start()

    def set_quote_card(content):
        quote_card.content = content
        page.update()

    page.add(
        page_title,
        ft.Row([ticker_input, load_button]),
        quote_card,
        ft.Divider(),
        nav_row,
        ft.Divider(),
        content_area
    )

    change_tab(0)

if __name__ == "__main__":
    ft.app(target=main)
