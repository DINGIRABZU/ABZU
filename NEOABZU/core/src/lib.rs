use pyo3::prelude::*;
use std::collections::VecDeque;

#[derive(Clone, Debug)]
pub enum Expr {
    Var(String),
    Lam(String, Box<Expr>),
    App(Box<Expr>, Box<Expr>),
}

impl std::fmt::Display for Expr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Expr::Var(v) => write!(f, "{}", v),
            Expr::Lam(arg, body) => write!(f, "\\{}.{}", arg, body),
            Expr::App(a, b) => write!(f, "({} {})", a, b),
        }
    }
}

fn parse(tokens: &mut VecDeque<char>) -> Expr {
    parse_app(tokens)
}

fn parse_app(tokens: &mut VecDeque<char>) -> Expr {
    let mut expr = parse_atom(tokens);
    loop {
        if let Some(&c) = tokens.front() {
            if c != ')' {
                let right = parse_atom(tokens);
                expr = Expr::App(Box::new(expr), Box::new(right));
            } else {
                break;
            }
        } else {
            break;
        }
    }
    expr
}

fn parse_atom(tokens: &mut VecDeque<char>) -> Expr {
    if let Some(c) = tokens.pop_front() {
        match c {
            '\\' => {
                let var = tokens.pop_front().expect("missing var").to_string();
                tokens.pop_front(); // skip '.'
                let body = parse(tokens);
                Expr::Lam(var, Box::new(body))
            }
            '(' => {
                let expr = parse(tokens);
                tokens.pop_front(); // skip ')'
                expr
            }
            _ => Expr::Var(c.to_string()),
        }
    } else {
        panic!("unexpected eof")
    }
}

fn substitute(expr: Expr, var: &str, val: &Expr) -> Expr {
    match expr {
        Expr::Var(ref v) if v == var => val.clone(),
        Expr::Var(_) => expr,
        Expr::Lam(arg, body) => {
            if arg == var {
                Expr::Lam(arg, body)
            } else {
                Expr::Lam(arg.clone(), Box::new(substitute(*body, var, val)))
            }
        }
        Expr::App(a, b) => Expr::App(
            Box::new(substitute(*a, var, val)),
            Box::new(substitute(*b, var, val)),
        ),
    }
}

fn eval(expr: Expr) -> Expr {
    match expr {
        Expr::App(f, x) => {
            let f = eval(*f);
            let x = eval(*x);
            if let Expr::Lam(arg, body) = f {
                eval(substitute(*body, &arg, &x))
            } else {
                Expr::App(Box::new(f), Box::new(x))
            }
        }
        Expr::Lam(arg, body) => Expr::Lam(arg, Box::new(eval(*body))),
        Expr::Var(_) => expr,
    }
}

/// Evaluate a lambda-calculus expression and return the resulting term as a string.
pub fn evaluate(src: &str) -> String {
    let mut chars: VecDeque<char> = src.chars().filter(|c| !c.is_whitespace()).collect();
    let expr = parse(&mut chars);
    let result = eval(expr);
    result.to_string()
}

#[pyfunction]
#[pyo3(name = "evaluate")]
fn evaluate_py(src: &str) -> PyResult<String> {
    Ok(evaluate(src))
}

#[pymodule]
fn neoabzu_core(_py: Python, m: &Bound<PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(evaluate_py, m)?)?;
    Ok(())
}
