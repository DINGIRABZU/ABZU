use httpmock::prelude::*;
use pyo3::prelude::*;
use pyo3::types::PyDict;

#[test]
fn razar_falls_back_to_kimicho_on_crown_error() {
    Python::with_gil(|py| {
        let server = MockServer::start();
        let _m = server.mock(|when, then| {
            when.method(POST).path("/");
            then.status(200)
                .header("content-type", "application/json")
                .body("{\"text\":\"pong\"}");
        });

        let code = format!(
            r#"
import neoabzu_crown as crown
import neoabzu_kimicho as k
k.init_kimicho('{url}')
crown.route_decision = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('down'))
def route():
    try:
        return crown.route_decision('ping', {{'emotion':'joy'}})
    except Exception:
        text = k.fallback_k2('ping')
        return {{'model':'kimicho', 'text': text}}
"#,
            url = server.url("/")
        );

        let razar = PyModule::from_code(py, &code, "", "razar_agent").unwrap();
        let res: &PyDict = razar
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
fn razar_falls_back_to_kimicho_when_crown_missing() {
    Python::with_gil(|py| {
        let server = MockServer::start();
        let _m = server.mock(|when, then| {
            when.method(POST).path("/");
            then.status(200)
                .header("content-type", "application/json")
                .body("{\"text\":\"pong\"}");
        });

        let code = format!(
            r#"
import sys
import neoabzu_kimicho as k
k.init_kimicho('{url}')
def route():
    sys.modules.pop('neoabzu_crown', None)
    try:
        import neoabzu_crown as crown
        return crown.route_decision('ping', {{'emotion':'joy'}})
    except Exception:
        text = k.fallback_k2('ping')
        return {{'model':'kimicho', 'text': text}}
"#,
            url = server.url("/")
        );

        let razar = PyModule::from_code(py, &code, "", "razar_agent").unwrap();
        let res: &PyDict = razar
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

