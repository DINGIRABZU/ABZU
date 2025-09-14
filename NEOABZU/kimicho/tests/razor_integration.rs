use httpmock::prelude::*;
use pyo3::prelude::*;

#[test]
fn razor_can_call_kimicho_fallback() {
    Python::with_gil(|py| {
        let server = MockServer::start();
        let _m = server.mock(|when, then| {
            when.method(POST).path("/");
            then.status(200)
                .header("content-type", "application/json")
                .body("{\"text\":\"pong\"}");
        });

        let code = format!(
            "import neoabzu_kimicho as k\n"
            "k.init_kimicho('{url}')\n"
            "def invoke():\n"
            "    return k.fallback_k2('ping')\n",
            url = server.url("/")
        );
        let razor = PyModule::from_code(py, &code, "", "razor_agent").unwrap();
        let res: String = razor
            .getattr("invoke")
            .unwrap()
            .call0()
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(res, "pong");
    });
}
