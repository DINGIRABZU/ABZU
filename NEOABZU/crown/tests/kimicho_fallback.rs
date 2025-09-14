use httpmock::prelude::*;
use pyo3::prelude::*;
use pyo3::types::PyDict;

#[test]
fn razor_falls_back_to_kimicho_on_crown_error() {
    Python::with_gil(|py| {
        let server = MockServer::start();
        let _m = server.mock(|when, then| {
            when.method(POST).path("/");
            then.status(200)
                .header("content-type", "application/json")
                .body("{\"text\":\"pong\"}");
        });

        let code = format!(
            "import neoabzu_crown as crown\n" \
            "import neoabzu_kimicho as k\n" \
            "k.init_kimicho('{url}')\n" \
            "crown.route_decision = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('down'))\n" \
            "def route():\n" \
            "    try:\n" \
            "        return crown.route_decision('ping', {'emotion':'joy'})\n" \
            "    except Exception:\n" \
            "        text = k.fallback_k2('ping')\n" \
            "        return {'model':'kimicho', 'text': text}\n",
            url = server.url("/")
        );

        let razor = PyModule::from_code(py, &code, "", "razor_agent").unwrap();
        let res: &PyDict = razor
            .getattr("route")
            .unwrap()
            .call0()
            .unwrap()
            .downcast()
            .unwrap();
        let model: String = res.get_item("model").unwrap().unwrap().extract().unwrap();
        assert_eq!(model, "kimicho");
        let text: String = res.get_item("text").unwrap().unwrap().extract().unwrap();
        assert_eq!(text, "pong");
    });
}

#[test]
fn razor_falls_back_to_kimicho_when_crown_missing() {
    Python::with_gil(|py| {
        let server = MockServer::start();
        let _m = server.mock(|when, then| {
            when.method(POST).path("/");
            then.status(200)
                .header("content-type", "application/json")
                .body("{\"text\":\"pong\"}");
        });

        let code = format!(
            "import sys\n" \
            "import neoabzu_kimicho as k\n" \
            "k.init_kimicho('{url}')\n" \
            "def route():\n" \
            "    sys.modules.pop('neoabzu_crown', None)\n" \
            "    try:\n" \
            "        import neoabzu_crown as crown\n" \
            "        return crown.route_decision('ping', {'emotion':'joy'})\n" \
            "    except Exception:\n" \
            "        text = k.fallback_k2('ping')\n" \
            "        return {'model':'kimicho', 'text': text}\n",
            url = server.url("/")
        );

        let razor = PyModule::from_code(py, &code, "", "razor_agent").unwrap();
        let res: &PyDict = razor
            .getattr("route")
            .unwrap()
            .call0()
            .unwrap()
            .downcast()
            .unwrap();
        let model: String = res.get_item("model").unwrap().unwrap().extract().unwrap();
        assert_eq!(model, "kimicho");
        let text: String = res.get_item("text").unwrap().unwrap().extract().unwrap();
        assert_eq!(text, "pong");
    });
}

