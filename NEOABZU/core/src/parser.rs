// Patent pending – see PATENTS.md
use super::{Element, Expr, ExprKind, Glyph};
use std::collections::VecDeque;

pub fn parse(tokens: &mut VecDeque<char>) -> Expr {
    parse_app(tokens)
}

fn parse_app(tokens: &mut VecDeque<char>) -> Expr {
    let mut expr = parse_atom(tokens);
    loop {
        if let Some(&c) = tokens.front() {
            if c != ')' {
                let right = parse_atom(tokens);
                let combined = expr.element.clone().or(right.element.clone());
                let momentum = expr.momentum + right.momentum;
                expr = Expr {
                    kind: ExprKind::App(Box::new(expr), Box::new(right)),
                    element: combined,
                    momentum,
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
                    momentum: body.momentum,
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
            _ => {
                let mut momentum = 0;
                if c == 'I' {
                    if let Some('[') = tokens.front() {
                        tokens.pop_front();
                        let mut tag = String::new();
                        while let Some(ch) = tokens.pop_front() {
                            if ch == ']' {
                                break;
                            }
                            tag.push(ch);
                        }
                        if tag.eq_ignore_ascii_case("an") {
                            momentum = 1;
                        }
                    }
                }
                Expr {
                    kind: ExprKind::Var(c.to_string()),
                    element: None,
                    momentum,
                }
            }
        }
    } else {
        panic!("unexpected eof")
    }
}
