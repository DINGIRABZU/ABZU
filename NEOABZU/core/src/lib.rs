use pyo3::prelude::*;
use std::collections::VecDeque;

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
        }
    }

    fn with_element(kind: ExprKind, element: Element) -> Self {
        Expr {
            kind,
            element: Some(element),
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

fn parse(tokens: &mut VecDeque<char>) -> Expr {
    parse_app(tokens)
}

fn parse_app(tokens: &mut VecDeque<char>) -> Expr {
    let mut expr = parse_atom(tokens);
    loop {
        if let Some(&c) = tokens.front() {
            if c != ')' {
                let right = parse_atom(tokens);
                let combined = expr.element.clone().or(right.element.clone());
                expr = Expr {
                    kind: ExprKind::App(Box::new(expr), Box::new(right)),
                    element: combined,
                };
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
                Expr {
                    element: body.element.clone(),
                    kind: ExprKind::Lam(var, Box::new(body)),
                }
            }
            '(' => {
                let expr = parse(tokens);
                tokens.pop_front(); // skip ')'
                expr
            }
            '@' => Expr::new(ExprKind::SelfRef),
            '🜂' => Expr::with_element(ExprKind::Glyph(Glyph::Flame), Element::Fire),
            '🜄' => Expr::with_element(ExprKind::Glyph(Glyph::Wave), Element::Water),
            '🜁' => Expr::with_element(ExprKind::Glyph(Glyph::Breeze), Element::Air),
            '🜃' => Expr::with_element(ExprKind::Glyph(Glyph::Stone), Element::Earth),
            _ => Expr::new(ExprKind::Var(c.to_string())),
        }
    } else {
        panic!("unexpected eof")
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
                }
            } else {
                let new_body = substitute(*body, var, val);
                Expr {
                    element: new_body.element.clone(),
                    kind: ExprKind::Lam(arg.clone(), Box::new(new_body)),
                }
            }
        }
        ExprKind::App(a, b) => {
            let new_a = substitute(*a, var, val);
            let new_b = substitute(*b, var, val);
            Expr {
                element: new_a.element.clone().or(new_b.element.clone()),
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
                    kind: ExprKind::App(Box::new(f), Box::new(x)),
                },
            }
        }
        ExprKind::Lam(arg, body) => {
            let lam = Expr {
                element: expr.element.clone(),
                kind: ExprKind::Lam(arg.clone(), body.clone()),
            };
            let eval_body = eval_with_self(*body, Some(lam.clone()));
            Expr {
                element: eval_body.element.clone(),
                kind: ExprKind::Lam(arg, Box::new(eval_body)),
            }
        }
        ExprKind::Var(_) => expr,
        ExprKind::SelfRef => self_ref.expect("SelfRef outside of lambda"),
        ExprKind::Glyph(_) => expr,
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
    use super::{eval, parse, evaluate, Element};
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
}

