use httpmock::prelude::*;
use pyo3::prelude::*;
use pyo3::types::PyDict;

#[test]
fn razar_falls_back_when_validator_blocks() {
    Python::with_gil(|py| {
        let server = MockServer::start();
        let _m = server.mock(|when, then| {
            when.method(POST).path("/");
            then.status(200)
                .header("content-type", "application/json")
                .body("{\"text\":\"pong\"}");
        });

        py.run("import sys; sys.path.append('../..')", None, None)
            .unwrap();
        let code = format!(
            r#"
import neoabzu_crown as crown
import neoabzu_kimicho as k
from INANNA_AI.ethical_validator import EthicalValidator

k.init_kimicho('{url}')
validator = EthicalValidator()

def route():
    try:
        return crown.route_decision('prepare to attack the village', {{'emotion': 'neutral'}}, validator=validator)
    except Exception:
        text = k.fallback_k2('ping')
        return {{'model': 'kimicho', 'text': text}}
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
