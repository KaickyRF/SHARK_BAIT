from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import pandas as pd
from sharkbait import extract, transform, custom_metrics, Deal, Base, load 
from requests.exceptions import HTTPError
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

#setting test_database: open a test table in memory
@pytest.fixture
def memory_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session
    session.close()
#database setting ends; test function in the end on file


@patch("sharkbait.requests.get")
def test_extract(mock_request):
    #test the conection with cheapshark API; simulates expected JSON response for games and store

    mock_response = MagicMock()
    mock_response.json.return_value = [
    {
        "dealID": "deal_001",
        "title": "A GAME FOR TEST",
        "storeID": "1",
        "salePrice": "10.00",
        "normalPrice": "100.00",
        "metacriticScore": "80",
        "steamRatingText": "Mostly Positive",
        "steamRatingPercent": "80",
        "thumb": "https://cheapshark.com/thumb.jpg"
    }
]
    
    mock_stores_response = MagicMock()
    mock_stores_response.json.return_value = [
        {
            "storeID": "1", 
            "storeName": "Steam"
        }
    ]

    mock_request.side_effect = [mock_response, mock_stores_response]
    data, stores = extract(page_size=1)
    assert data == [
    {
        "dealID": "deal_001",
        "title": "A GAME FOR TEST",
        "storeID": "1",
        "salePrice": "10.00",
        "normalPrice": "100.00",
        "metacriticScore": "80",
        "steamRatingText": "Mostly Positive",
        "steamRatingPercent": "80",
        "thumb": "https://cheapshark.com/thumb.jpg"
    }
]

    assert stores == [
        {
            "storeID": "1", 
            "storeName": "Steam"
        }
    ]


@patch("sharkbait.requests.get")
def test_extract_error(mock_request_error):
    #test that the function raises an exception if the conection fails
    mock_request_error.side_effect = HTTPError("No response from the API")
    with pytest.raises(HTTPError):
        extract()


def test_transform():
    #test the data pipeline processing; sends the expected estructure from extract; types undefined
    expensive_fish = [
    {
        "dealID": "deal_101",
        "title": "Expensive delicious game",
        "storeID": "1",
        "salePrice": "1.99",
        "normalPrice": "9.99",
        "metacriticScore": "95",
        "steamRatingText": "Overwhelmingly Positive",
        "steamRatingPercent": "98",
        "thumb": "https://cheapshark.com/thumb1.jpg"
    },
    {
        "dealID": "deal_102",
        "title": "Cheap good game",
        "storeID": "1",
        "salePrice": "2.99",
        "normalPrice": "9.99",
        "metacriticScore": "89",
        "steamRatingText": "Very Positive",
        "steamRatingPercent": "94",
        "thumb": "https://cheapshark.com/thumb2.jpg"
    }
]
    expensive_store = [
    {"storeID": "1", "storeName": "Steam"}
]
    
    framedata = transform(expensive_fish, expensive_store)

    assert isinstance(framedata, pd.DataFrame)

    assert "title" in framedata.columns
    assert "shop" in framedata.columns

    assert framedata.iloc[0]["shop"] == "Steam"


def test_custom_metrics():
    #test the internal metrics and features creation; use a data structure expected from transform function; types defined
    cheap_fish = {
    "dealID": ["deal_001", "deal_002"],
    "title": ["Shark", "Fish"],
    "price_now": [1.99, 50.00],
    "normal_price": [10.00, 100.00],
    "savings": [80.1, 50.0],
    "metacritic": [95.0, 70.0],
    "steam_rate_percent": [98.0, 60.0]
    }

    frame_data = pd.DataFrame(cheap_fish)
    
    bait_frame = custom_metrics(frame_data)

    assert "critic_steam" in bait_frame.columns
    assert "sort_rate_price" in bait_frame.columns
    assert "savings" in bait_frame.columns

    assert bait_frame.iloc[0]["title"] == "Shark"
    assert bait_frame.iloc[0]["critic_steam"] == 97.10
    assert bait_frame.iloc[0]["savings"] == 80.1
    assert bait_frame.iloc[0]["sort_rate_price"] == 100.00 #104.36 but the score limit is 100.00

    assert bait_frame.iloc[1]["title"] == "Fish"
    assert bait_frame.iloc[1]["critic_steam"] == 63.00
    assert bait_frame.iloc[1]["savings"] == 50.00
    assert bait_frame.iloc[1]["sort_rate_price"] == 53.42

#database test
@patch("sharkbait.SessionLocal")
def test_database_save(mock_session_local, memory_session):
    #tests that the load function is recording a correct table in database; check data types

    mock_session_local.return_value = memory_session

    df_test = pd.DataFrame([
    {
        "dealID": "abc123xyz_test",
        "title": "Cyberpunk Test Game",
        "shop": "Steam",
        "price_now": 19.99,
        "normal_price": 59.99,
        "metacritic": 86.0,
        "steam_rate": "Very Positive",
        "steam_rate_percent": 88.0,
        "critic_steam": 87.4,       
        "sort_rate_price": 85.2,   
        "thumb": "https://images.example.com/thumb.jpg",
        "savings": 66.68,           
        "updated_at": datetime.now(timezone.utc)
    }
])

    load(df_test)
    deal_bait = memory_session.query(Deal).filter_by(dealID="abc123xyz_test").first()
    
    assert deal_bait is not None
    assert deal_bait.title == "Cyberpunk Test Game"
    assert deal_bait.price_now == 19.99
    assert deal_bait.steam_rate == "Very Positive"
    assert deal_bait.critic_steam == 87.4
    assert deal_bait.sort_rate_price == 85.2
    assert deal_bait.thumb == "https://images.example.com/thumb.jpg"
    assert deal_bait.updated_at is not datetime.now(timezone.utc)

    #test that load function upsert logic works; receive same game, by dealID, then updates the data (price_now in this case)
    df_test2 = pd.DataFrame(
    [
        {
        "dealID": "abc123xyz_test",
        "title": "Cyberpunk Test Game",
        "shop": "Steam",
        "price_now": 9.99,
        "normal_price": 59.99,
        "metacritic": 86.0,
        "steam_rate": "Very Positive",
        "steam_rate_percent": 88.0,
        "critic_steam": 87.4,       
        "sort_rate_price": 85.2,   
        "thumb": "https://images.example.com/thumb.jpg",
        "savings": 66.68,           
        "updated_at": datetime.now(timezone.utc)
        }
    ]
)

    load(df_test2)
    deal_bait2 = memory_session.query(Deal).filter_by(dealID="abc123xyz_test").first()
        
    assert deal_bait2 is not None
    assert deal_bait2.dealID == "abc123xyz_test"
    assert deal_bait2.price_now == 9.99

@patch("sharkbait.SessionLocal")
def test_database_save_data(mock_session_local):
    #asserting data integrity error rollback; if the response is unexpected, interrupt the table modeling
    #raises an real error by sending incomplete data (missing price_now column)

    mock_session_rollback = MagicMock()
    mock_session_local.return_value = mock_session_rollback

    df_test_error = pd.DataFrame(
            [
                {
                "dealID": "abc123xyz_test",
                "title": "Cyberpunk Test Game",
                "shop": "Steam",
                "normal_price": 59.99,
                "metacritic": 86.0,
                "steam_rate": "Very Positive",
                "steam_rate_percent": 88.0,
                "critic_steam": 87.4,       
                "sort_rate_price": 85.2,   
                "thumb": "https://images.example.com/thumb.jpg",
                "savings": 66.68,           
                "updated_at": datetime.now(timezone.utc)
                }
            ]
        )


    load(df_test_error)
    mock_session_rollback.rollback.assert_called_once()

    
@patch("sharkbait.SessionLocal")
def test_database_save_database(mock_session_local):
    #asserting database conection error rollback; if the DB recording raises an error/harm databases, interrupt the modeling
    #raises an forced SQLite error with a mock, to force the exception
    mock_session_rollback = MagicMock()
    mock_session_local.return_value = mock_session_rollback
    mock_session_rollback.execute.side_effect = Exception("Erro de conexão no Database")

    df_test_baseerror = pd.DataFrame(
            [
                {
                "dealID": "abc123xyz_test",
                "title": "Cyberpunk Test Game",
                "shop": "Steam",
                "price_now": 19.99,
                "normal_price": 59.99,
                "metacritic": 86.0,
                "steam_rate": "Very Positive",
                "steam_rate_percent": 88.0,
                "critic_steam": 87.4,       
                "sort_rate_price": 85.2,   
                "thumb": "https://images.example.com/thumb.jpg",
                "savings": 66.68,           
                "updated_at": datetime.now(timezone.utc)
                }
            ]
        )


    load(df_test_baseerror)
    mock_session_rollback.rollback.assert_called_once()