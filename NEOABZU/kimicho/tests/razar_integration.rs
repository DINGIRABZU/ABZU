use httpmock::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

#[test]
fn razar_can_call_kimicho_fallback() {
    Python::with_gil(|py| {
        let server = MockServer::start();
        let _m = server.mock(|when, then| {
            when.method(POST).path("/");
            then.status(200)
                .header("content-type", "application/json")
                .body("{\"text\":\"pong\"}");
        });

        let code = format!(
            "import neoabzu_kimicho as k\n\
             k.init_kimicho('{url}')\n\
             def invoke():\n\
                 return k.fallback_k2('ping')\n",
            url = server.url("/")
        );
        let razar = PyModule::from_code(py, &code, "", "razar_agent").unwrap();
        let res: String = razar
            .getattr("invoke")
            .unwrap()
            .call0()
            .unwrap()
            .extract()
            .unwrap();
        assert_eq!(res, "pong");
    });
}

#[test]
fn razar_reports_kimicho_errors() {
    Python::with_gil(|py| {
        let server = MockServer::start();
        let _m = server.mock(|when, then| {
            when.method(POST).path("/");
            then.status(500);
        });

        let code = format!(
            "import neoabzu_kimicho as k\n\
             k.init_kimicho('{url}')\n\
             def invoke():\n\
                 return k.fallback_k2('ping')\n",
            url = server.url("/")
        );
        let razar = PyModule::from_code(py, &code, "", "razar_agent").unwrap();
        let err = razar
            .getattr("invoke")
            .unwrap()
            .call0()
            .unwrap_err();
        assert!(err.is_instance_of::<PyRuntimeError>(py));
    });
}
