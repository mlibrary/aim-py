import requests


def test_response():
    response = requests.get("http://google.com")
    assert (response.status_code) == 200
