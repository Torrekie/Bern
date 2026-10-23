//! Generated private build helper. Drivers already link libSystem. Keep the
//! remaining response-file tokens in their original spelling and order.
use std::{collections::BTreeSet, env, fs};
fn filtered(source: &str) -> String {
    let mut tokens = Vec::new();
    let mut start = None;
    let mut quote = None;
    let mut escaped = false;
    for (index, ch) in source.char_indices() {
        if start.is_none() && !ch.is_whitespace() {
            start = Some(index);
        }
        if escaped {
            escaped = false;
            continue;
        }
        if ch == '\\' {
            escaped = true;
            continue;
        }
        if let Some(delimiter) = quote {
            if ch == delimiter {
                quote = None;
            }
        } else if ch == '\'' || ch == '"' {
            quote = Some(ch);
        } else if ch.is_whitespace() {
            if let Some(at) = start.take() {
                tokens.push(&source[at..index]);
            }
        }
    }
    if let Some(at) = start {
        tokens.push(&source[at..]);
    }
    let mut seen = BTreeSet::new();
    tokens
        .into_iter()
        .filter(|token| {
            !matches!(*token, "-lSystem" | "-lSystem.B")
                && (!token.starts_with("-l") || seen.insert((*token).to_string()))
        })
        .collect::<Vec<_>>()
        .join(" ")
        + "\n"
}
fn main() -> std::io::Result<()> {
    let path = env::args_os()
        .nth(1)
        .expect("native libraries response file");
    let source = fs::read_to_string(&path)?;
    fs::write(path, filtered(&source))
}
#[cfg(test)]
mod tests {
    use super::filtered;
    #[test]
    fn driver_system_duplicates_removed_and_quoted_arguments_preserved() {
        assert_eq!(
            filtered("-lSystem -lobjc -lm -lSystem -lm -framework \"A  B\" -L'with path'\n"),
            "-lobjc -lm -framework \"A  B\" -L'with path'\n"
        );
    }
}
