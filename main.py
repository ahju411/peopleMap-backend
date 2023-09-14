from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import xml.etree.ElementTree as ET
import uvicorn
import json
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import cachetools

app = FastAPI()

cache = cachetools.TTLCache(maxsize=100, ttl=3600)

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("API_KEY must be set in the .env file.")
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/businfo/{bus_no}")
async def getBusInfo(bus_no: str):
    URL = f"http://ws.bus.go.kr/api/rest/busRouteInfo/getBusRouteList?serviceKey={API_KEY}&strSrch={bus_no}"
    print(f"Fetching: {URL}")

    r = requests.get(URL)

    if r.status_code == 200:
        try:
            root = ET.fromstring(r.content)

            item_list = []
            for item in root.findall(".//itemList"):
                item_data = {}
                for child in item:
                    item_data[child.tag] = child.text
                item_list.append(item_data)

            return {"itemList": item_list}

        except ET.ParseError:
            print("Failed to parse XML. Response content:")
            print(r.text)
            raise HTTPException(status_code=500, detail="Failed to parse XML from server")

    else:
        print(f"Received unexpected status code {r.status_code}: {r.text}")
        raise HTTPException(status_code=r.status_code, detail="Failed to fetch data from server")


'''params는 nx=12&ny=124 의 형태로 와야함'''


@app.get("/api/weather/nx={nx}&ny={ny}")
# @cachetools.cached(cache)
async def getWeather(nx: int, ny: int):
    # Get current time
    now = datetime.now()

    # Calculate base_date and base_time
    if now.minute <= 30:
        base_time = f"{now.hour - 1:02}00"
    else:
        base_time = f"{now.hour:02}00"

    if now.hour == 0 and now.minute <= 30:  # Edge case for midnight
        now = now - timedelta(days=1)  # Subtract a day to get the previous day's date

    base_date = now.strftime("%Y%m%d")

    URL = f"https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst?serviceKey={API_KEY}&pageNo=1&numOfRows=100&dataType=JSON&base_date={base_date}&base_time={base_time}&nx={nx}&ny={ny}"
    print(URL)

    r = requests.get(URL)
    if r.status_code == 200:
        response_data = r.json()  # Parse the JSON response
        print(response_data)
        print(URL)
        items = response_data["response"]["body"]["items"]
        return items
    else:
        print(f"Received unexpected status code {r.status_code}: {r.text}")
        raise HTTPException(status_code=r.status_code, detail="Failed to fetch data from server")

@app.get("/debug/cache")
def view_cache():
    cache_contents = dict(cache)
    for key, value in cache_contents.items():
        print(f"Key: {key}, Value: {value}")
    return {"status": "Cache contents printed to console"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
