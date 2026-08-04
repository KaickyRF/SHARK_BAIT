import sys

import requests
from fastapi import FastAPI

import pandas as pd
import sqlite3
from sqlalchemy import Column, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


app = FastAPI()
base = declarative_base()

def main():
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)

    data, stores = extract()
    frame = transform(data, stores)
    if len(sys.argv) > 1:
        path = sys.argv[1].strip()
        if not path.endswith(".csv"):
            path = path + ".csv"
        load(frame, path)
    else: 
        load(frame)
    
def extract(page_size=60):
    """
    Get the deals games from cheapshark API; also use the endpoint stores to get the storeName for storeID
    
    :param page_size: gives the lenght of games that de API will return; the maximum and default is 60
    :return: two JSON, one with a list of dicts of the games and another similar with the storeID and respective storeName
    :raises: requests.exceptions.HTTPError if failed to contact API
    """
    headers = {
        "User-Agent": "SharkBait/1.0 (CS50P Final Project)"
    }
    response = requests.get(f"https://www.cheapshark.com/api/1.0/deals?pageSize={page_size}", 
                            headers=headers)
    response.raise_for_status()
    data = response.json()


    store_response = requests.get("https://www.cheapshark.com/api/1.0/stores", 
                                  headers=headers)
    store_response.raise_for_status()
    stores = store_response.json()

    return data, stores


def transform(data, stores):
    """
    Turns data into pd.DataFrame and cleans, such as tranforming datatype and cleaning nulls
    and changing storeID for its name

    :param data: a JSON from Cheapshark API, list of dicts for each game
    :param stores: a JSON from Cheapshark API, list of dicts for each store
    :return: a game offer pd.DataFrame with structured data and builtin metrics
        """
    
    essential = ["title", "storeID","salePrice", "normalPrice", "metacriticScore", "steamRatingText", "steamRatingPercent"]
    rename = {
    "title": "Title",
    "storeID": "Shop",
    "salePrice": "Price_now",
    "normalPrice": "Normal_price",
    "metacriticScore": "Metacritic",
    "steamRatingText": "Steam_rate",
    "steamRatingPercent": "Steam_rate(%)"
    }
    #Create the structure (dict) to change storeID for its name later
    s = pd.DataFrame(stores)
    dicts_store = s.set_index("storeID")["storeName"].to_dict()

    d = pd.DataFrame(data)
    frame0 = d[essential]
    frame1 = frame0.rename(columns=rename)

    frame1["Price_now"] = frame1["Price_now"].astype(float)
    frame1["Metacritic"] = frame1["Metacritic"].astype(float)
    frame1["Steam_rate(%)"] = frame1["Steam_rate(%)"].astype(float)
    frame1["Normal_price"]= frame1["Normal_price"].astype(float)


    frame1["Shop"] = frame1["Shop"].map(dicts_store)
    frame2 = frame1.reset_index(drop=True)
    frame2["Steam_rate"] = frame2["Steam_rate"].fillna("No Reviews")

    frame3 = custom_metrics(frame2)

    return frame3

def custom_metrics(frame1):
    """
    A extend for Transforming the data, assuming duplicate delete,
    adding business metrics for average game rating and a avg score 
    with rating and price - using it to sort; also round decimals for 2
     
    :param frame1: a pd.DataFrame with Cheapshark API games
    :return: a pd.DataFrame with custom metrics in columns, sorted by Rate|Price """
    #Create a custom metric, use all rate data for average data Critic|Steam, priorize user rating
    frame1["Critic|Steam"] = (frame1["Metacritic"] * 0.3) + (frame1["Steam_rate(%)"] * 0.7)
    frame1.loc[frame1["Metacritic"] == 0, "Critic|Steam"] = frame1["Steam_rate(%)"] * 0.9

    #Create a custom metric, use previous avg rating with an avg Rate|Price and sort with it
    frame1["Sort by Rate|Price"] = frame1["Critic|Steam"] - (frame1["Price_now"] * 0.1)
    frame2 = frame1.sort_values(by="Sort by Rate|Price", ascending=False)
    frame2 = frame2.drop_duplicates(subset="Title", keep="first")

    frame2["Critic|Steam"] = frame2["Critic|Steam"].round(2)
    frame2["Sort by Rate|Price"] = frame2["Sort by Rate|Price"].round(2)
    frame2["Price_now"] = frame2["Price_now"].round(2)

    return frame2

def load(frame, path="shark_offers_now.csv"):
    """
    Create a CSV archive from a pd.DataFrame with game offers
    
    :param frame: a pd.DataFrame with structured offers from Cheapshark API
    :param path: a str for the archive path and name; if there is no path given create in the same folder with 
    default name
    :return: 'Successful load' for feedback and a CSV file or exception error message
    """
    try:
        frame.to_csv(path, index=False)
        print(f"Successful load of {path}")

    except Exception as error:
        print(f"An load error ocurred: {error}")


if __name__ == "__main__":
    main()