import httpx
import pytest

from um_world_model.arcgis import ArcGISClient, ArcGISError


def test_pagination_and_count_reconciliation():
    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        if request.url.path.endswith("/0"):
            return httpx.Response(
                200, json={"objectIdField": "OID", "maxRecordCount": 2}
            )
        if params.get("returnCountOnly") == "true":
            return httpx.Response(200, json={"count": 3})
        offset = int(params.get("resultOffset", "0"))
        rows = [
            {"attributes": {"OID": oid}} for oid in ([1, 2] if offset == 0 else [3])
        ]
        return httpx.Response(200, json={"features": rows})

    with ArcGISClient(transport=httpx.MockTransport(handler)) as client:
        pages = list(client.pages("https://example.test/FeatureServer/0", "1=1"))
    assert [len(page.features) for page in pages] == [2, 1]


def test_pagination_rejects_early_empty_page():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/0"):
            return httpx.Response(
                200, json={"objectIdField": "OID", "maxRecordCount": 2}
            )
        if request.url.params.get("returnCountOnly") == "true":
            return httpx.Response(200, json={"count": 1})
        return httpx.Response(200, json={"features": []})

    with (
        ArcGISClient(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(ArcGISError, match="pagination stopped"),
    ):
        list(client.pages("https://example.test/FeatureServer/0", "1=1"))


def test_source_http_failure_is_not_silenced():
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(503, text="unavailable")
    )
    with (
        ArcGISClient(transport=transport) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        client.layer_metadata("https://example.test/FeatureServer/0")
