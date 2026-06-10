from backend.services.curl_parser import parse_curl


def test_parse_simple_get():
    spec = parse_curl("curl https://api.example.com/users")
    assert spec.method == "GET"
    assert spec.url == "https://api.example.com/users"


def test_parse_without_curl_prefix():
    spec = parse_curl("https://api.example.com/users")
    assert spec.url == "https://api.example.com/users"


def test_parse_method_and_headers():
    spec = parse_curl('curl -X POST https://api.example.com/login -H "Content-Type: application/json" -H "Authorization: Bearer abc"')
    assert spec.method == "POST"
    headers = {h.key: h.value for h in spec.headers}
    assert headers["Content-Type"] == "application/json"
    assert headers["Authorization"] == "Bearer abc"


def test_parse_data_implies_post_and_json():
    spec = parse_curl('curl https://x.com -H "content-type: application/json" --data-raw \'{"a":1}\'')
    assert spec.method == "POST"
    assert spec.body == '{"a":1}'
    assert spec.body_type == "json"


def test_parse_data_non_json_is_raw():
    spec = parse_curl("curl https://x.com -d hello")
    assert spec.method == "POST"
    assert spec.body == "hello"
    assert spec.body_type == "raw"


def test_parse_multiline_continuation():
    text = "curl https://x.com \\\n  -X PUT \\\n  -H 'A: 1'"
    spec = parse_curl(text)
    assert spec.method == "PUT"
    assert spec.url == "https://x.com"
    assert spec.headers[0].key == "A"


def test_parse_url_flag():
    spec = parse_curl("curl --url https://x.com/a")
    assert spec.url == "https://x.com/a"
