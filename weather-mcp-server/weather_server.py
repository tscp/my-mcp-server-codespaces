import json
import urllib.request
import urllib.parse
from typing import Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Weather MCP Server")

def fetch_weather_data(latitude: float, longitude: float) -> Dict[str, Any]:
    """Open-Meteo JMA API から天気データを取得する"""
    base_url = "https://api.open-meteo.com/v1/jma"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,weathercode,windspeed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "hourly": "temperature_2m,weather_code,precipitation",
        "timezone": "Asia/Tokyo",
        "forecast_days": 7
    }
    # URL エンコード
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        return data
    except Exception as e:
        return {"error": f"APIリクエストに失敗しました: {str(e)}"}

def weather_code_to_description(code: int) -> str:
    """WMO天気コードを日本語の説明に変換する"""
    weather_descriptions = {
        0: "晴れ",
        1: "主に晴れ",
        2: "一部曇り",
        3: "曇り",
        45: "霧",
        48: "霧氷",
        51: "弱い雨滴",
        53: "中程度の雨滴",
        55: "強い雨滴",
        56: "弱い凍雨滴",
        57: "強い凍雨滴",
        61: "弱い雨",
        63: "中程度の雨",
        65: "強い雨",
        66: "弱い凍雨",
        67: "強い凍雨",
        71: "弱い雪",
        73: "中程度の雪",
        75: "強い雪",
        77: "雪粒子",
        80: "弱いにわか雨",
        81: "中程度のにわか雨",
        82: "強いにわか雨",
        85: "弱いにわか雪",
        86: "強いにわか雪",
        95: "雷雨",
        96: "軽度の雷雨とひょう",
        99: "激しい雷雨とひょう"
    }
    return weather_descriptions.get(code, f"不明な天気コード: {code}")

@mcp.tool()
def get_current_weather(latitude: float, longitude: float, location_name: str = "指定地点") -> dict:
    """指定された座標の天気を取得する
    
    Args:
        latitude: 緯度(例: 東京 35.6762)
        longitude: 経度(例: 東京 139.6503)
        location_name: 地点名（表示用）
    """
    data = fetch_weather_data(latitude, longitude)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    if "error" in data:
        return data
    
    current = data.get("current", {})
    return {
        "location": location_name,
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "temperature": f"{current.get('temperature_2m', 'N/A')}°C",
        "humidity": f"{current.get('relative_humidity_2m', 'N/A')}%",
        "weather": weather_code_to_description(current.get("weather_code", 0)),
        "windspeed": f"{current.get('windspeed_10m', 'N/A')} km/h",
        "weather_code": current.get("weather_code")
    }

@mcp.tool()
def get_weekly_forecast(latitude: float, longitude: float, location_name: str = "指定地点") -> dict:
    """指定された座標の週間天気予報を取得する
    
    Args:
        latitude: 緯度(例: 東京 35.6762)
        longitude: 経度(例: 東京 139.6503)
        location_name: 地点名（表示用）
    """
    data = fetch_weather_data(latitude, longitude)

    if "error" in data:
        return data
    
    daily = data.get("daily", {})
    times = daily.get("time", [])
    weather_codes = daily.get("weather_code", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    precipitation = daily.get("precipitation_sum", [])

    forecast = []
    for i in range(len(times)):
        day_data = {
            "date": times[i],
            "weather": weather_code_to_description(weather_codes[i]) if i < len(weather_codes) else "不明",
            "temparature_max": f"{temp_max[i]}°C" if i < len(temp_max) else "N/A",
            "temparature_min": f"{temp_min[i]}°C" if i < len(temp_min) else "N/A",
            "precipitation": f"{precipitation[i]} mm" if i < len(precipitation) else "N/A"
        }
        forecast.append(day_data)
    
    return {
        "location": location_name,
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "forecast_period": "7日間",
        "forecast": forecast
    }

@mcp.tool()
def get_today_hourly_weather(latitude: float, longitude: float, location_name: str = "指定地点") -> dict:
    """指定された座標の本日の1時間ごとの天気を取得する
    
    Args:
        latitude: 緯度(例: 東京 35.6762)
        longitude: 経度(例: 東京 139.6503)
        location_name: 地点名（表示用）
    """
    data = fetch_weather_data(latitude, longitude)

    if "error" in data:
        return data
    
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    codes = hourly.get("weather_code", [])
    precs = hourly.get("precipitation", [])

    if not times:
        return {"error": "時間データが取得できませんでした。"}
    
    # API レスポンスのタイムゾーン
    tz_name = data.get("timezone", "Asia/Tokyo")
    try:
        today_str = datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d")
    except Exception:
        today_str = datetime.now().strftime("%Y-%m-%d")
    
    def build_hours_for(day_prefix: str):
        hours: list[dict[str, Any]] = []
        for i, t in enumerate(times):
            if isinstance(t, str) and t.startswith(day_prefix):
                item = {
                    "time": t,
                    "temperature": f"{temps[i]}°C" if i < len(temps) else "N/A",
                    "weather": weather_code_to_description(codes[i]) if i < len(codes) else "不明",
                    "weader_code": codes[i] if i < len(codes) else None,
                    "precipitation": f"{precs[i]} mm" if i < len(precs) else "N/A"
                }
                hours.append(item)
        return hours
    
    hours = build_hours_for(today_str)

    if not hours:
        current_time = data.get("current", {}).get("time")
        if isinstance(current_time, str) and len(current_time) >= 10:
            hours = build_hours_for(current_time[:10])
    return {
        "location": location_name,
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "date": today_str,
        "hours": hours
    }

if __name__ == "__main__":
    print("Starting MCP Server...")
    mcp.run(transport="streamable-http")