from database import Base, engine, SessionLocal
from models import Deal

import requests
import pandas as pd
from sqlalchemy.dialects.sqlite import insert

def main():
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)

    data, stores = extract()
    frame = transform(data, stores)
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
    response = requests.get(f"https://www.cheapshark.com/api/1.0/deals?pageSize={page_size}", headers=headers)
    response.raise_for_status()
    data = response.json()


    store_response = requests.get("https://www.cheapshark.com/api/1.0/stores", headers=headers)
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
    
    essential = ["dealID", "title", "storeID","salePrice", "normalPrice",
    "metacriticScore", "steamRatingText", "steamRatingPercent", "thumb"]
    
    rename = {
    'dealID': 'dealID',
    'title': 'title',
    'storeID': 'shop',
    'salePrice': 'price_now',
    'normalPrice': 'normal_price',
    'metacriticScore': 'metacritic',
    'steamRatingText': 'steam_rate',
    'steamRatingPercent': 'steam_rate_percent',
    'thumb': 'thumb'}
    #Create the structure (dict) to change storeID for its name later
    s = pd.DataFrame(stores)
    dicts_store = s.set_index("storeID")["storeName"].to_dict()

    d = pd.DataFrame(data)
    frame0 = d[essential]
    frame1 = frame0.rename(columns=rename)

    frame1["price_now"] = frame1["price_now"].astype(float)
    frame1["metacritic"] = frame1["metacritic"].astype(float)
    frame1["steam_rate_percent"] = frame1["steam_rate_percent"].astype(float)
    frame1["normal_price"]= frame1["normal_price"].astype(float)


    frame1["shop"] = frame1["shop"].map(dicts_store)
    frame2 = frame1.reset_index(drop=True)
    frame2["steam_rate"] = frame2["steam_rate"].fillna("No Reviews")

    frame3 = custom_metrics(frame2)

    return frame3

def custom_metrics(frame1):
    """
    A extend for Transforming the data, assuming duplicate delete,
    adding business metrics for average game rating and a avg score 
    with rating and price - using it to sort; also round decimals for 2
     
    :param frame1: a pd.DataFrame with Cheapshark API games
    :return: a pd.DataFrame with custom metrics in columns, sorted by Rate|Price """
    #Create a custom metric, use all rate data for average data critic_steam, priorize user rating
    frame1["critic_steam"] = (frame1["metacritic"] * 0.3) + (frame1["steam_rate_percent"] * 0.7)
    frame1.loc[frame1["metacritic"] == 0, "critic_steam"] = frame1["steam_rate_percent"] * 0.9

    #Create a custom metric, use previous avg rating with an avg Rate|Price and sort with it
    frame1["sort_rate_price"] = frame1["critic_steam"] - (frame1["price_now"] * 0.1)
    frame2 = frame1.sort_values(by="sort_rate_price", ascending=False)
    frame2 = frame2.drop_duplicates(subset="dealID", keep="first")

    frame2["critic_steam"] = frame2["critic_steam"].round(2)
    frame2["sort_rate_price"] = frame2["sort_rate_price"].round(2)
    frame2["price_now"] = frame2["price_now"].round(2)

    return frame2

def load(frame):
    """Saves or updates game offers from a pandas DataFrame into the SQLite database.

    Performs an UPSERT (insert or update) operation using the 'dealID' as
    the constraint key. If a deal already exists in the database, it
    updates its prices, ratings, and metrics; otherwise, it inserts it as
    a new row.

    :param frame: A pandas DataFrame containing structured offers from the
    CheapShark API.
    :type frame: pd.DataFrame
    :return: None
    :raises Exception: Rolls back the transaction and logs an error if the
    database operation fails.
    """

    #Create/update SQL table
    Base.metadata.create_all(bind=engine)
    records = frame.to_dict(orient="records")

    session = SessionLocal()
    try:
        for record in records:
            sttmt = insert(Deal).values(**record)

            sttmt = sttmt.on_conflict_do_update(
                index_elements=[Deal.dealID],
                set_={
                    "price_now": record["price_now"],
                    "normal_price": record["normal_price"],
                    "metacritic": record["metacritic"],
                    "steam_rate": record["steam_rate"],
                    "steam_rate_percent": record["steam_rate_percent"],
                    "critic_steam": record["critic_steam"],
                    "sort_rate_price": record["sort_rate_price"],
                    "thumb": record["thumb"],
                },
            )
            session.execute(sttmt)
        session.commit()
        print(f"{len(records)} deals insert into SQLite")

    except Exception as e:
        session.rollback()
        print(f"Error in the SQLite insert: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    main()