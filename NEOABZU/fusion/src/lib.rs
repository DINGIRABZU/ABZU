//! Invariance fusion engine connecting symbolic and numeric realms.
use pyo3::prelude::*;

#[pyclass]
#[derive(Clone, Debug)]
pub struct Invariant {
    /// Lambda calculus output, if present.
    #[pyo3(get, set)]
    pub lambda: Option<String>,
    /// Numerical eigenvector, if present.
    #[pyo3(get, set)]
    pub eigenvector: Option<Vec<f64>>,
}

#[pymethods]
impl Invariant {
    #[new]
    fn new(lambda: Option<String>, eigenvector: Option<Vec<f64>>) -> Self {
        Self {
            lambda,
            eigenvector,
        }
    }
}

/// Selects the invariant with the highest inevitability gradient.
#[cfg_attr(feature = "tracing", tracing::instrument)]
#[pyfunction]
pub fn fuse(pairs: Vec<(Invariant, f64)>) -> PyResult<Invariant> {
    let best = pairs
        .into_iter()
        .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(inv, _)| inv)
        .unwrap_or_else(|| Invariant {
            lambda: None,
            eigenvector: None,
        });
    Ok(best)
}

#[pymodule]
fn neoabzu_fusion(_py: Python, m: &Bound<PyModule>) -> PyResult<()> {
    m.add_class::<Invariant>()?;
    m.add_function(wrap_pyfunction!(fuse, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn chooses_highest_gradient() {
        let sym = Invariant {
            lambda: Some("λx.x".into()),
            eigenvector: None,
        };
        let num = Invariant {
            lambda: None,
            eigenvector: Some(vec![1.0, 0.0]),
        };
        let res = fuse(vec![(sym.clone(), 0.2), (num.clone(), 0.9)]).unwrap();
        assert!(res.eigenvector.is_some());
    }
}
