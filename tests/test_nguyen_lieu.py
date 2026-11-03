from tests.du_lieu_mau import tao_du_lieu

URL = "/api/v1/nguyen-lieu"


def test_list_nguyen_lieu(client, db_session):
    tao_du_lieu(db_session)
    assert [n["tenNguyenLieu"] for n in client.get(URL).json()] == ["Thịt bò", "Tôm"]
    ds = client.get(URL, params={"q": "TÔM"}).json()
    assert len(ds) == 1 and ds[0]["nhomNguyenLieu"] == "hải sản" and "idNguyenLieu" in ds[0]
    assert len(client.get(URL, params={"size": 1}).json()) == 1
    assert client.get(URL, params={"size": 0}).status_code == 422
