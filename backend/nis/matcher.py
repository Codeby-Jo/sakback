def get_dummy_matches(user_id: int):
    """
    Dummy NIS Integration
    Until Ghaniim finishes NIS, this will return fake matches
    so the Frontend and Backend can be tested.
    """
    return [
        {
            "user_id": 2,
            "name": "Fatima",
            "score": 95
        },
        {
            "user_id": 3,
            "name": "Ayesha",
            "score": 88
        }
    ]
