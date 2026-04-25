import pytest
from httpx import AsyncClient

async def test_get_balance(client, auth_headers):
    response = await client.get("/billing/balance", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "balance_stars" in data

async def test_get_payments(client, auth_headers):
    response = await client.get("/billing/payments", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

async def test_get_tariffs(client):
    response = await client.get("/billing/tariffs")
    assert response.status_code == 200