use neoabzu_fusion::{fuse, Invariant};
use pyo3::Python;

#[test]
fn returns_empty_when_no_pairs() {
    Python::with_gil(|py| {
        let res = fuse(py, Vec::new()).unwrap();
        assert!(res.lambda.is_none());
        assert!(res.eigenvector.is_none());
    });
}
