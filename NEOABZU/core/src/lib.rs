//! Core lambda-calculus evaluation engine for NeoABZU.
//!
//! Enable the `tracing` feature to emit spans and `opentelemetry` to export
//! them:
//!
//! ```bash
//! cargo test -p neoabzu-core --features opentelemetry
//! ```
use pyo3::prelude::*;
use std::collections::VecDeque;

pub mod sacred;
mod evaluator;
mod parser;
pub use evaluator::reduce_inevitable;
pub use parser::parse;
pub use sacred::axioms::{PrimordialPrinciple, ABSOLUTE_YES};

#[derive(Clone, Debug, PartialEq)]
pub enum Element {
    Fire,
    Water,
    Air,
    Earth,
}

#[derive(Clone, Debug, PartialEq)]
pub enum Glyph {
    Flame,
    Wave,
    Breeze,
    Stone,
}

impl Glyph {
    fn element(&self) -> Element {
        match self {
            Glyph::Flame => Element::Fire,
            Glyph::Wave => Element::Water,
            Glyph::Breeze => Element::Air,
            Glyph::Stone => Element::Earth,
        }
    }

    fn as_char(&self) -> char {
        match self {
            Glyph::Flame => '🜂',
            Glyph::Wave => '🜄',
            Glyph::Breeze => '🜁',
            Glyph::Stone => '🜃',
        }
    }
}

#[derive(Clone, Debug)]
pub struct Expr {
    kind: ExprKind,
    element: Option<Element>,
    momentum: i32,
}

#[derive(Clone, Debug)]
pub enum ExprKind {
    Var(String),
    Lam(String, Box<Expr>),
    App(Box<Expr>, Box<Expr>),
    SelfRef,
    Glyph(Glyph),
}

impl Expr {
    fn new(kind: ExprKind) -> Self {
        Expr {
            kind,
            element: None,
            momentum: 0,
        }
    }

    fn with_element(kind: ExprKind, element: Element) -> Self {
        Expr {
            kind,
            element: Some(element),
            momentum: 0,
        }
    }
}

impl std::fmt::Display for Expr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match &self.kind {
            ExprKind::Var(v) => write!(f, "{}", v),
            ExprKind::Lam(arg, body) => write!(f, "\\{}.{}", arg, body),
            ExprKind::App(a, b) => write!(f, "({} {})", a, b),
            ExprKind::SelfRef => write!(f, "@"),
            ExprKind::Glyph(g) => write!(f, "{}", g.as_char()),
        }
    }
}

fn substitute(expr: Expr, var: &str, val: &Expr) -> Expr {
    match expr.kind {
        ExprKind::Var(ref v) if v == var => val.clone(),
        ExprKind::Var(_) => expr,
        ExprKind::Lam(arg, body) => {
            if arg == var {
                Expr {
                    kind: ExprKind::Lam(arg, body),
                    element: expr.element,
                    momentum: expr.momentum,
                }
            } else {
                let new_body = substitute(*body, var, val);
                Expr {
                    element: new_body.element.clone(),
                    momentum: new_body.momentum,
                    kind: ExprKind::Lam(arg.clone(), Box::new(new_body)),
                }
            }
        }
        ExprKind::App(a, b) => {
            let new_a = substitute(*a, var, val);
            let new_b = substitute(*b, var, val);
            Expr {
                element: new_a.element.clone().or(new_b.element.clone()),
                momentum: new_a.momentum + new_b.momentum,
                kind: ExprKind::App(Box::new(new_a), Box::new(new_b)),
            }
        }
        ExprKind::SelfRef => expr,
        ExprKind::Glyph(_) => expr,
    }
}

fn eval(expr: Expr) -> Expr {
    eval_with_self(expr, None)
}

fn eval_with_self(expr: Expr, self_ref: Option<Expr>) -> Expr {
    match expr.kind {
        ExprKind::App(f, x) => {
            let f = eval_with_self(*f.clone(), self_ref.clone());
            let x = eval_with_self(*x, self_ref.clone());
            match f.kind.clone() {
                ExprKind::Lam(arg, body) => {
                    let body_sub = substitute(*body, &arg, &x);
                    eval_with_self(body_sub, Some(f))
                }
                ExprKind::Glyph(g) => {
                    let mut result = x;
                    result.element = Some(g.element());
                    result
                }
                _ => Expr {
                    element: f.element.clone().or(x.element.clone()),
                    momentum: f.momentum + x.momentum,
                    kind: ExprKind::App(Box::new(f), Box::new(x)),
                },
            }
        }
        ExprKind::Lam(arg, body) => {
            let lam = Expr {
                element: expr.element.clone(),
                momentum: expr.momentum,
                kind: ExprKind::Lam(arg.clone(), body.clone()),
            };
            let eval_body = eval_with_self(*body, Some(lam.clone()));
            Expr {
                element: eval_body.element.clone(),
                momentum: eval_body.momentum,
                kind: ExprKind::Lam(arg, Box::new(eval_body)),
            }
        }
        ExprKind::Var(_) => expr,
        ExprKind::SelfRef => self_ref.expect("SelfRef outside of lambda"),
        ExprKind::Glyph(_) => expr,
    }
}

/// Evaluate a lambda-calculus expression and return the resulting term as a string.
#[cfg_attr(feature = "tracing", tracing::instrument)]
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
    m.add_function(wrap_pyfunction!(evaluator::reduce_inevitable_py, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{eval, evaluate, parse, Element};
    use std::collections::VecDeque;

    #[test]
    fn self_ref_returns_function() {
        assert_eq!(evaluate("(\\x.@)a"), "\\x.\\x.@");
    }

    #[test]
    fn self_ref_expands_in_body() {
        assert_eq!(evaluate("\\x.@"), "\\x.\\x.@");
    }

    #[test]
    fn glyph_application_sets_metadata() {
        let mut chars: VecDeque<char> = "🜂x".chars().collect();
        let expr = parse(&mut chars);
        let result = eval(expr);
        assert!(matches!(result.element, Some(Element::Fire)));
    }

    #[test]
    fn application_reduces() {
        assert_eq!(evaluate("(\\x.x)y"), "y");
    }
    #[test]
    fn phoneme_tag_sets_momentum() {
        let mut chars: VecDeque<char> = "I[AN]".chars().collect();
        let expr = parse(&mut chars);
        assert_eq!(expr.momentum, 1);
    }

}
