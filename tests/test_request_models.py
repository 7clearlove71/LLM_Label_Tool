import pytest
from pydantic import ValidationError

from backend.models import RequestSpec, ResponseResult, RequestStore, KeyValueItem


def test_request_spec_defaults():
    spec = RequestSpec()
    assert spec.method == "GET"
    assert spec.url == ""
    assert spec.params == []
    assert spec.headers == []
    assert spec.body_type == "none"
    assert spec.body == ""
    assert spec.form_body == []


def test_request_store_defaults():
    store = RequestStore()
    assert store.samples == []
    assert store.draft is None


def test_key_value_item_default_enabled():
    item = KeyValueItem(key="k", value="v")
    assert item.enabled is True


def test_response_result_error_shape():
    r = ResponseResult(error="boom")
    assert r.status is None
    assert r.error == "boom"


def test_request_spec_rejects_invalid_body_type():
    with pytest.raises(ValidationError):
        RequestSpec(body_type="binary")


def test_request_store_active_id_default():
    store = RequestStore()
    assert store.active_id is None
