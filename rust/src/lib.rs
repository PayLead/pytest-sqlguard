use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use sql_insight::sqlparser::dialect::GenericDialect;

#[pyfunction]
fn normalize_sql(sql: &str) -> PyResult<String> {
    let dialect = GenericDialect {};
    let normalized_queries = sql_insight::normalize(&dialect, sql).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("SQL normalization error: {}", e))
    })?;
    let first_query = normalized_queries[0].clone();
    Ok(first_query)
}

#[pyfunction]
fn format_sql(sql: &str) -> PyResult<String> {
    let dialect = GenericDialect {};
    let formatted_queries = sql_insight::format(&dialect, sql).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("SQL formatting error: {}", e))
    })?;
    let first_query = formatted_queries[0].clone();
    Ok(first_query)
}

#[pymodule]
fn sqlrs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(normalize_sql, m)?)?;
    m.add_function(wrap_pyfunction!(format_sql, m)?)?;
    Ok(())
}
