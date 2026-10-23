//! Execute the native formatter and compare it with the protocol's formatter.
#![cfg(target_os = "macos")]

use bern_protocol::format::{self, Arg};
use serde_json::{Value, json};
use std::collections::BTreeMap;
use std::io::Write;
use std::path::Path;
use std::process::{Command, Stdio};

struct Case {
    pattern: &'static str,
    language: &'static str,
    args: Vec<(&'static str, Arg)>,
}

fn number(value: f64) -> Arg {
    Arg::Number {
        value,
        text: if value.fract() == 0.0 && value < i64::MAX as f64 {
            (value as i64).to_string()
        } else {
            value.to_string()
        },
    }
}

fn names(language: &str) -> BTreeMap<String, String> {
    format::date_names()
        .into_iter()
        .map(|(key, translations)| {
            let text = translations
                .iter()
                .find(|(candidate, _)| *candidate == language)
                .or_else(|| {
                    translations
                        .iter()
                        .find(|(candidate, _)| *candidate == "en")
                })
                .map(|(_, text)| text.clone())
                .unwrap_or_default();
            (key, text)
        })
        .collect()
}

fn arg_json(arg: &Arg) -> Value {
    match arg {
        Arg::Text(text) => json!(text),
        Arg::Number { value, text } => json!({ "number": value, "text": text }),
        Arg::Date { year, month, day } => json!({ "year": year, "month": month, "day": day }),
    }
}

#[test]
fn foundation_formatter_matches_protocol_messages_dates_and_durations() {
    let mut cases = vec![
        Case {
            pattern: "已播放 {count} 集 {{x}} 🎬",
            language: "zh-Hans",
            args: vec![("count", number(3.0))],
        },
        Case {
            pattern: "{user}: {missing} {{value}}",
            language: "en",
            args: vec![("user", Arg::Text("Zoë 👩🏽‍💻".into()))],
        },
        Case {
            pattern: "{n, plural, =01 {leading zero} one {one} other {other}}",
            language: "en",
            args: vec![("n", number(1.0))],
        },
        Case {
            pattern: "{n, plural, one {# item} other {# items}}",
            language: "en",
            args: vec![(
                "n",
                Arg::Number {
                    value: 1.0,
                    text: "1.00".into(),
                },
            )],
        },
        Case {
            pattern: "{n, plural, one {{m, plural, one {# child} other {# children}} in # group} other {# groups}}",
            language: "en",
            args: vec![("n", number(1.0)), ("m", number(2.0))],
        },
        Case {
            pattern: "{d}",
            language: "en",
            args: vec![(
                "d",
                Arg::Date {
                    year: 7,
                    month: 1,
                    day: 2,
                },
            )],
        },
    ];
    let plural = "{n, plural, =0 {no episodes} one {# episode} other {# episodes}}";
    for language in ["en", "zh-Hans", "ja", "ko", "vi", "th", "id", "ms", "en_US"] {
        for n in [0.0, 1.0, 2.0, 12.0, 1.5, -1.0] {
            cases.push(Case {
                pattern: plural,
                language,
                args: vec![("n", number(n))],
            });
        }
    }
    for language in ["en", "zh-Hans", "zh-Hant", "ja"] {
        for (year, month, day) in [(2026, 10, 12), (2000, 1, 1), (2024, 2, 29), (-4, 2, 29)] {
            for pattern in [
                "{d, date, EEE, MMM d}",
                "{d, date, EEEE yyyy-MM-dd}",
                "{d, date, yy/M/d}",
                "{d, date, MMMM dd}",
            ] {
                cases.push(Case {
                    pattern,
                    language,
                    args: vec![("d", Arg::Date { year, month, day })],
                });
            }
        }
    }
    for seconds in [-1.0, 0.0, 59.9, 555.0, 3725.0, 66600.0, 1.0e40] {
        for pattern in [
            "{t, duration, m:ss}",
            "{t, duration, h:mm:ss}",
            "{t, duration, hh:mm}",
            "{t, duration, s}",
        ] {
            cases.push(Case {
                pattern,
                language: "en",
                args: vec![("t", number(seconds))],
            });
        }
    }
    let requests: Vec<Value> = cases.iter().map(|case| json!({
        "pattern": case.pattern,
        "language": case.language,
        "args": case.args.iter().map(|(key, value)| ((*key).into(), arg_json(value))).collect::<BTreeMap<String, Value>>(),
        "names": names(case.language),
    })).collect();
    let expected: Vec<String> = cases
        .iter()
        .map(|case| {
            let pieces = format::parse(case.pattern).expect("fixture is a valid protocol message");
            let translations = names(case.language);
            format::format(
                &pieces,
                case.language,
                &|key| {
                    case.args
                        .iter()
                        .find(|(candidate, _)| *candidate == key)
                        .map(|(_, arg)| arg.clone())
                },
                &|key| translations.get(key).cloned().unwrap_or_default(),
            )
        })
        .collect();

    let crate_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let output = crate_dir.join("../../target/bern-test/objc-format");
    std::fs::create_dir_all(&output).unwrap();
    let source = output.join("formatter.m");
    let executable = output.join("formatter");
    std::fs::write(&source, RUNNER).unwrap();
    let triple = if cfg!(target_arch = "aarch64") {
        "arm64-apple-macos11.0"
    } else {
        "x86_64-apple-macos11.0"
    };
    let compile = Command::new("xcrun")
        .args([
            "--sdk",
            "macosx",
            "clang",
            "-target",
            triple,
            "-fobjc-arc",
            "-fblocks",
            "-Werror=unguarded-availability",
            "-Werror=unguarded-availability-new",
            "-framework",
            "Foundation",
            "-I",
        ])
        .arg(crate_dir.join("templates"))
        .arg(&source)
        .arg("-o")
        .arg(&executable)
        .output()
        .unwrap();
    assert!(
        compile.status.success(),
        "native formatter did not compile:\n{}",
        String::from_utf8_lossy(&compile.stderr)
    );
    let mut child = Command::new(&executable)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(&serde_json::to_vec(&requests).unwrap())
        .unwrap();
    let result = child.wait_with_output().unwrap();
    assert!(
        result.status.success(),
        "native formatter failed:\n{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let actual: Vec<String> =
        serde_json::from_slice(&result.stdout).expect("native results are valid JSON");
    assert_eq!(actual.len(), expected.len());
    for (index, (actual, expected)) in actual.iter().zip(expected.iter()).enumerate() {
        assert_eq!(
            actual, expected,
            "fixture {index}: {} ({})",
            cases[index].pattern, cases[index].language
        );
    }
}

const RUNNER: &str = r#"
#import <Foundation/Foundation.h>
#include <math.h>
#include <stdint.h>
static BOOL BNIsNull(id value) { return value == nil || value == [NSNull null]; }
static NSString *BNString(id value) { return BNIsNull(value) ? @"" : [value isKindOfClass:[NSString class]] ? value : [value description]; }
#include "BernText.inc"
int main(void) {
    @autoreleasepool {
        NSData *data = [[NSFileHandle fileHandleWithStandardInput] readDataToEndOfFile];
        NSArray *requests = [NSJSONSerialization JSONObjectWithData:data options:0 error:NULL];
        if (![requests isKindOfClass:[NSArray class]]) return 2;
        NSMutableArray *results = [NSMutableArray array];
        for (NSDictionary *request in requests) {
            NSDictionary *names = request[@"names"];
            [results addObject:BNFormat(request[@"pattern"], request[@"args"], request[@"language"], ^NSString *(NSString *key) { return names[key] ?: @""; })];
        }
        NSData *output = [NSJSONSerialization dataWithJSONObject:results options:0 error:NULL];
        [[NSFileHandle fileHandleWithStandardOutput] writeData:output];
    }
    return 0;
}
"#;
