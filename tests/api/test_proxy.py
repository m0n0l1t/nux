async def test_get_proxy(client, auth_headers):
    response = await client.get("/proxy", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Может вернуть пустой объект или данные
    assert isinstance(data, dict)