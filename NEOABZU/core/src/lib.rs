use pyo3::prelude::*;
use std::collections::VecDeque;

#[derive(Clone, Debug)]
pub enum Expr {
    Var(String),
    Lam(String, Box<Expr>),
    App(Box<Expr>, Box<Expr>),
    SelfRef,
}

impl std::fmt::Display for Expr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Expr::Var(v) => write!(f, "{}", v),
            Expr::Lam(arg, body) => write!(f, "\\{}.{}", arg, body),
            Expr::App(a, b) => write!(f, "({} {})", a, b),
            Expr::SelfRef => write!(f, "@"),
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
            '@' => Expr::SelfRef,
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
        Expr::SelfRef => Expr::SelfRef,
    }
}

fn eval(expr: Expr) -> Expr {
    eval_with_self(expr, None)
}

fn eval_with_self(expr: Expr, self_ref: Option<Expr>) -> Expr {
    match expr {
        Expr::App(f, x) => {
            let f = eval_with_self(*f.clone(), self_ref.clone());
            let x = eval_with_self(*x, self_ref.clone());
            if let Expr::Lam(arg, body) = f.clone() {
                let body_sub = substitute(*body, &arg, &x);
                eval_with_self(body_sub, Some(f))
            } else {
                Expr::App(Box::new(f), Box::new(x))
            }
        }
        Expr::Lam(arg, body) => {
            let lam = Expr::Lam(arg.clone(), body.clone());
            Expr::Lam(arg, Box::new(eval_with_self(*body, Some(lam))))
        }
        Expr::Var(_) => expr,
        Expr::SelfRef => self_ref.expect("SelfRef outside of lambda"),
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

#[cfg(test)]
mod tests {
    use super::evaluate;

    #[test]
    fn self_ref_returns_function() {
        assert_eq!(evaluate("(\\x.@)a"), "\\x.\\x.@");
    }

    #[test]
    fn self_ref_expands_in_body() {
        assert_eq!(evaluate("\\x.@"), "\\x.\\x.@");
    }
}
