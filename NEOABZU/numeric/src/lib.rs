//! Numeric utilities including Principal Component Analysis.

use ndarray::{Array1, Array2, Axis};
use numpy::{PyArray2, PyReadonlyArray2};
use pyo3::prelude::*;

fn pca(data: &Array2<f64>, n_components: usize) -> Array2<f64> {
    let n_features = data.ncols();
    let mut centered = data.clone();
    // center columns
    let means = centered.mean_axis(Axis(0)).unwrap();
    for mut row in centered.rows_mut() {
        row -= &means;
    }
    // covariance matrix
    let mut cov_matrix = centered.t().dot(&centered) / (centered.nrows() as f64 - 1.0);
    let mut components: Vec<f64> = Vec::with_capacity(n_components * n_features);
    for _ in 0..n_components {
        let mut v = Array1::<f64>::from_elem(n_features, 1.0);
        v /= (v.dot(&v)).sqrt();
        for _ in 0..100 {
            let mut v_new = cov_matrix.dot(&v);
            let norm = (v_new.dot(&v_new)).sqrt();
            if norm > 0.0 {
                v_new /= norm;
            }
            v = v_new;
        }
        components.extend(v.iter().copied());
        // deflation
        let lambda = v.dot(&cov_matrix.dot(&v));
        let outer = v.clone().insert_axis(Axis(1)).dot(&v.clone().insert_axis(Axis(0)));
        cov_matrix -= &(outer * lambda);
    }
    Array2::from_shape_vec((n_components, n_features), components).unwrap()
}

#[pyfunction]
fn find_principal_components(
    py: Python<'_>,
    data: PyReadonlyArray2<f64>,
    n_components: usize,
) -> PyResult<Py<PyArray2<f64>>> {
    let arr = data.as_array();
    let comps = pca(&arr.to_owned(), n_components);
    Ok(PyArray2::from_owned_array(py, comps).into_py(py))
}

#[pymodule]
fn neoabzu_numeric(_py: Python, m: &Bound<PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_principal_components, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::pca;
    use ndarray::arr2;

    #[test]
    fn principal_component_direction() {
        let data = arr2(&[[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]]);
        let comps = pca(&data, 1);
        let v = comps.row(0);
        let expected = arr2(&[[0.4472135955, 0.894427191]]);
        let dot = v.dot(&expected.row(0)).abs();
        assert!((dot - 1.0).abs() < 1e-6);
    }
}
