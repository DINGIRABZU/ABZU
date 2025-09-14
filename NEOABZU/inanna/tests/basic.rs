use pyo3::prelude::*;

#[test]
fn spell_invocation_works() {
    Python::with_gil(|_| {
        let res = neoabzu_inanna::invoke_spell("x").unwrap();
        assert_eq!(res, "spell:x");
    });
}
