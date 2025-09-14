use nalgebra::{DMatrix, SymmetricEigen};
use pyo3::prelude::*;
use tracing::instrument;

/// Find principal components of the provided data matrix.
///
/// `data` is expected to be a list of observations, each with the same
/// number of features. `components` specifies how many principal
/// components to return. The function is exposed to Python via PyO3.
#[pyfunction]
#[instrument]
pub fn find_principal_components(
    data: Vec<Vec<f64>>,
    components: usize,
) -> PyResult<Vec<Vec<f64>>> {
    if data.is_empty() {
        return Ok(Vec::new());
    }
    let rows = data.len();
    let cols = data[0].len();
    let flat: Vec<f64> = data.into_iter().flatten().collect();
    let matrix = DMatrix::from_row_slice(rows, cols, &flat);
    let mean: Vec<f64> = (0..cols)
        .map(|j| matrix.column(j).sum() / rows as f64)
        .collect();
    let centered = DMatrix::from_fn(rows, cols, |i, j| matrix[(i, j)] - mean[j]);
    let cov = (&centered.transpose() * &centered) / (rows as f64 - 1.0);
    let eig = SymmetricEigen::new(cov);
    let mut pairs: Vec<(f64, Vec<f64>)> = eig
        .eigenvalues
        .iter()
        .zip(eig.eigenvectors.column_iter())
        .map(|(val, vec)| (*val, vec.iter().cloned().collect()))
        .collect();
    pairs.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());
    Ok(pairs.into_iter().take(components).map(|(_, v)| v).collect())
}

/// PyO3 module initializer.
#[pymodule]
fn numeric(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    let _ = neoabzu_instrumentation::init_tracing("numeric");
    m.add_function(wrap_pyfunction!(find_principal_components, m)?)?;
    Ok(())
}
