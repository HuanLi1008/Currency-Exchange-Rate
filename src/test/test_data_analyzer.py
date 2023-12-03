from src.main.data_analyzer import analyz

def test_data_analyzer():
    fake_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    response = analyz(fake_data)

    assert response["min"] == 1
    assert response["max"] == 10
    assert response["average"] == 5.5