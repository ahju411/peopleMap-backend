from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import xml.etree.ElementTree as ET
import uvicorn
import json
from dotenv import load_dotenv
import os

app = FastAPI()

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

@app.get("/busRoute/{bus_no}")
async def getBusRouteInfo(bus_no: str):
    URL = f"http://ws.bus.go.kr/api/rest/busRouteInfo/getStaionByRoute?serviceKey={API_KEY}&busRouteId={bus_no}"
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

            for item in item_list:
                section_id = item.get("direction")
                item["busDirection"] = "U" if section_id == "홍대입구역" else "D"

            return {"itemList": item_list}

        except ET.ParseError:
            print("Failed to parse XML. Response content:")
            print(r.text)
            raise HTTPException(status_code=500, detail="Failed to parse XML from server")

    else:
        print(f"Received unexpected status code {r.status_code}: {r.text}")
        raise HTTPException(status_code=r.status_code, detail="Failed to fetch data from server")



@app.get("/busRealTime/{bus_no}")
async def getBusInfo(bus_no: str):
    URL = f"http://ws.bus.go.kr/api/rest/buspos/getBusPosByRtid?serviceKey={API_KEY}&busRouteId={bus_no}"
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

            route_item_list = await getBusRouteInfo(bus_no)
            route_item_list = route_item_list.get("itemList", [])

            section_to_direction = {item.get("section"): item.get("direction") for item in route_item_list}

            for item in item_list:
                section_id = item.get("sectionId")
                direction = section_to_direction.get(section_id, "Unknown")
                item["busDirection"] = "U" if direction == "홍대입구역" else "D"

            return {"itemList": item_list}

        except ET.ParseError:
            print("Failed to parse XML. Response content:")
            print(r.text)
            raise HTTPException(status_code=500, detail="Failed to parse XML from server")

    else:
        print(f"Received unexpected status code {r.status_code}: {r.text}")
        raise HTTPException(status_code=r.status_code, detail="Failed to fetch data from server")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
