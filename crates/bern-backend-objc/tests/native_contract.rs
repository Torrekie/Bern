#[allow(dead_code)]
#[path = "../templates/native_links.rs"]
mod native_links;
use bern_backend_objc::{Frontend, NativeTarget, Platform, native_files};
use bern_target_api::{BuildContext, BuildStep, Framework, Run, Target};
use std::path::{Path, PathBuf};

fn project() -> (bern_compiler::Config, bern_compiler::Compiled) {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap();
    let config = bern_compiler::config::load(&root.join("examples/hello/Bern.toml")).unwrap();
    let compiled = bern_compiler::compile(&config).unwrap();
    (config, compiled)
}
fn context(
    config: &bern_compiler::Config,
    compiled: &bern_compiler::Compiled,
    platform: &str,
) -> BuildContext {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap();
    BuildContext {
        project_dir: config.dir.clone(),
        workspace_dir: root.clone(),
        output_dir: root.join("target/bern-test/native-contract"),
        target: bern_target_api::TargetConfig {
            platform: platform.into(),
            ..Default::default()
        },
        protocol_package: config.protocol_package.name.clone(),
        protocol_path: config.protocol_package.dir.clone(),
        protocol_module: compiled.protocol_module.clone(),
        engine_package: config.engine_package.name.clone(),
        engine_path: config.engine_package.dir.clone(),
        engine_type: config.engine_type.clone(),
        modules: vec![],
        framework: Framework::Path(root.join("crates")),
        release: false,
    }
}
fn file<'a>(files: &'a [bern_target_api::GeneratedFile], path: &str) -> &'a [u8] {
    &files
        .iter()
        .find(|f| f.path == Path::new(path))
        .unwrap()
        .contents
}
#[test]
fn both_languages_use_identical_renderer_model_and_engine_glue() {
    let (config, compiled) = project();
    for platform in [Platform::Macos, Platform::Ios] {
        let context = context(
            &config,
            &compiled,
            if platform == Platform::Macos {
                "macos"
            } else {
                "ios"
            },
        );
        let objc = NativeTarget::new(platform, Frontend::ObjectiveC)
            .generate(&compiled.app, &context)
            .unwrap();
        let swift = NativeTarget::new(platform, Frontend::SwiftUi)
            .generate(&compiled.app, &context)
            .unwrap();
        for path in [
            "Sources/BernNative.h",
            "Sources/BernNative.m",
            "Sources/BernModel.inc",
            "Sources/BernRenderer.inc",
            "Sources/BernMotion.inc",
            "Sources/BernGestures.inc",
            "Sources/BernNavigation.inc",
            "Sources/BernSearch.inc",
            "Sources/BernDrop.inc",
            "Sources/BernFeatures.inc",
            "Sources/BernQueries.inc",
            "Sources/BernMedia.inc",
            "Sources/BernText.inc",
            "glue/src/lib.rs",
            "glue/src/native_links.rs",
        ] {
            assert_eq!(file(&objc, path), file(&swift, path), "shared input {path}");
        }
        assert!(
            !objc
                .iter()
                .any(|f| f.path.extension().is_some_and(|e| e == "swift"))
        );
        let shell = std::str::from_utf8(file(&swift, "Sources/BernHost.swift")).unwrap();
        assert!(!shell.contains("Observation"));
        assert!(!shell.contains("@Observable"));
    }
}
#[test]
fn model_transports_unicode_and_includes_framework_date_names() {
    let (_, compiled) = project();
    let files = native_files(&compiled.app);
    let model = std::str::from_utf8(file(&files, "Sources/BernModel.inc")).unwrap();
    let encoded = model
        .split("{\n")
        .nth(1)
        .unwrap()
        .split("};")
        .next()
        .unwrap();
    let bytes = encoded
        .split(',')
        .filter_map(|s| s.trim().parse::<u8>().ok())
        .collect::<Vec<_>>();
    let value: serde_json::Value = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(
        value["app"]["name"],
        serde_json::to_value(&compiled.app.app.name).unwrap()
    );
    assert!(
        value["texts"]
            .as_array()
            .unwrap()
            .iter()
            .any(|t| t["key"] == "bern.query.loading")
    );
    assert!(
        value["texts"]
            .as_array()
            .unwrap()
            .iter()
            .any(|t| t["key"].as_str().unwrap().contains("month"))
    );
}
#[test]
fn deployment_and_link_plans_separate_language_from_renderer_and_device_from_simulator() {
    let (config, compiled) = project();
    for platform in [Platform::Macos, Platform::Ios] {
        for frontend in [Frontend::ObjectiveC, Frontend::SwiftUi] {
            let mut context = context(
                &config,
                &compiled,
                if platform == Platform::Macos {
                    "macos"
                } else {
                    "ios"
                },
            );
            for device in [false, true] {
                if platform == Platform::Macos && device {
                    continue;
                }
                context.target.destination =
                    Some(if device { "device" } else { "simulator" }.into());
                let plan = NativeTarget::new(platform, frontend)
                    .plan(&compiled.app, &context)
                    .unwrap();
                let runs = plan
                    .steps
                    .iter()
                    .filter_map(|step| {
                        if let BuildStep::Run { program, args, .. } = step {
                            Some((program, args))
                        } else {
                            None
                        }
                    })
                    .collect::<Vec<_>>();
                let compile = runs
                    .iter()
                    .find(|(_, args)| args.iter().any(|arg| arg.ends_with("BernNative.m")))
                    .unwrap();
                assert!(compile.1.iter().any(|arg| arg == "-fobjc-arc"));
                assert!(
                    compile
                        .1
                        .iter()
                        .any(|arg| arg.contains(if platform == Platform::Macos {
                            "macos11.0"
                        } else {
                            "ios14.0"
                        }))
                );
                let link = runs
                    .iter()
                    .find(|(_, args)| args.iter().any(|arg| arg == "-lbern_app"))
                    .unwrap();
                assert!(
                    link.1
                        .windows(2)
                        .any(|v| v == ["-Xlinker", "-fatal_warnings"])
                );
                assert!(
                    runs.iter()
                        .any(|(program, args)| program.ends_with("_bern_link_flags")
                            && args.len() == 1
                            && args[0].ends_with("native-libs"))
                );
                assert!(
                    link.1
                        .windows(2)
                        .any(|v| v == ["-framework", "CoreGraphics"])
                );
                assert_eq!(
                    link.1.iter().any(|arg| arg == "swiftc"),
                    frontend == Frontend::SwiftUi
                );
                if frontend == Frontend::SwiftUi {
                    assert!(link.1.windows(2).any(|v| v == ["-swift-version", "5"]));
                }
                assert!(
                    !link
                        .1
                        .iter()
                        .any(|arg| arg == "-no_warn_duplicate_libraries")
                );
                if device {
                    assert!(plan.run.is_none());
                    assert!(compile.1.iter().any(|arg| arg == "iphoneos"));
                    assert!(compile.1.iter().any(|arg| arg == "arm64-apple-ios14.0"));
                } else if platform == Platform::Ios {
                    assert!(matches!(plan.run, Some(Run::Simulator { .. })));
                }
            }
        }
    }
}

#[cfg(target_os = "macos")]
#[test]
fn native_runtime_typechecks_at_both_deployment_baselines() {
    use std::{fs, process::Command};
    let (_, mut compiled) = project();
    compiled.app.windows.windows[0].content = bern_ir::Node::Element(bern_ir::Element {
        kind: "Svg".into(),
        id: None,
        path: "main.svg".into(),
        props: [(
            "source".into(),
            bern_ir::Prop::Resource {
                name: "test.svg".into(),
            },
        )]
        .into(),
        template: None,
        children: vec![],
        action: None,
        source: Default::default(),
    });
    let dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../target/bern-test/native-availability");
    fs::create_dir_all(&dir).unwrap();
    for file in native_files(&compiled.app) {
        let path = dir.join(&file.path);
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(path, file.contents).unwrap();
    }
    for (sdk, triple) in [
        ("macosx", "arm64-apple-macos11.0"),
        ("iphonesimulator", "arm64-apple-ios14.0-simulator"),
        ("iphoneos", "arm64-apple-ios14.0"),
    ] {
        let output = Command::new("xcrun")
            .args([
                "--sdk",
                sdk,
                "clang",
                "-target",
                triple,
                "-fobjc-arc",
                "-fblocks",
                "-fsyntax-only",
                "-Werror=unguarded-availability",
                "-Werror=unguarded-availability-new",
            ])
            .arg(dir.join("Sources/BernNative.m"))
            .output()
            .expect("Xcode command tools");
        assert!(
            output.status.success(),
            "native {triple}: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
}

#[cfg(target_os = "macos")]
#[test]
fn foundation_codec_matches_rust_for_every_value_shape_and_rejects_bad_tags() {
    use bern_protocol::{EnumDef, FieldDef, RecordDef, Type, Value, VariantDef, Writer};
    use std::{
        fs,
        io::Write,
        process::{Command, Stdio},
    };
    let (_, mut compiled) = project();
    let field = |name: &str, ty: Type| FieldDef {
        name: name.into(),
        ty,
        doc: String::new(),
        content: false,
    };
    compiled.app.types.enums.push(EnumDef {
        name: "NativeChoice".into(),
        variants: vec![
            VariantDef {
                name: "Empty".into(),
                fields: vec![],
                label: None,
            },
            VariantDef {
                name: "Named".into(),
                fields: vec![field("name", Type::Text), field("count", Type::Int)],
                label: None,
            },
        ],
    });
    compiled.app.types.records.push(RecordDef {
        name: "NativeRecord".into(),
        fields: vec![
            field("id", Type::Int),
            field(
                "choice",
                Type::Enum {
                    name: "NativeChoice".into(),
                },
            ),
            field("note", Type::optional(Type::Text)),
        ],
    });
    let cases = vec![
        (Type::Unit, Value::Unit),
        (Type::Bool, Value::Bool(false)),
        (Type::Bool, Value::Bool(true)),
        (Type::Int, Value::Int(i64::MIN)),
        (Type::Int, Value::Int(i64::MAX)),
        (Type::Float, Value::Float(-123.12345678901234)),
        (Type::Float, Value::Float(-0.0)),
        (Type::Float, Value::Float(1.0e-308)),
        (Type::Float, Value::Float(1.0e308)),
        (Type::Text, Value::Text("你好 👩🏽‍💻 \0 \"\\\n".into())),
        (Type::optional(Type::Text), Value::none()),
        (
            Type::optional(Type::Text),
            Value::some(Value::Text("note".into())),
        ),
        (
            Type::list(Type::Int),
            Value::List(vec![Value::Int(-1), Value::Int(0), Value::Int(1)]),
        ),
        (
            Type::Enum {
                name: "NativeChoice".into(),
            },
            Value::Enum {
                variant: 1,
                fields: vec![Value::Text("payload".into()), Value::Int(-42)],
            },
        ),
        (
            Type::Record {
                name: "NativeRecord".into(),
            },
            Value::Record(vec![
                Value::Int(9),
                Value::unit_variant(0),
                Value::some(Value::Text("record".into())),
            ]),
        ),
    ];
    fn native(v: &Value) -> serde_json::Value {
        match v {
            Value::Unit | Value::Optional(None) => serde_json::Value::Null,
            Value::Bool(x) => serde_json::json!(x),
            Value::Int(x) => serde_json::json!(x),
            Value::Float(x) => serde_json::json!(x),
            Value::Text(x) => serde_json::json!(x),
            Value::Optional(Some(x)) => native(x),
            Value::List(x) | Value::Record(x) => {
                serde_json::Value::Array(x.iter().map(native).collect())
            }
            Value::Enum { variant, fields } => {
                serde_json::json!({"variant":variant,"fields":fields.iter().map(native).collect::<Vec<_>>()})
            }
        }
    }
    let mut inputs = vec![];
    let mut expected = vec![];
    for (ty, value) in cases {
        let mut writer = Writer::new();
        bern_protocol::encode(&value, &ty, &compiled.app.types, &mut writer);
        inputs.push(serde_json::json!({"type":ty,"bytes":writer.bytes}));
        expected.push(serde_json::json!({"value":native(&value),"bytes":writer.bytes}));
    }
    inputs.push(serde_json::json!({"type":{"kind":"bool"},"bytes":[2]}));
    expected.push(serde_json::json!({"error":"invalid_data"}));
    inputs
        .push(serde_json::json!({"type":{"kind":"optional","inner":{"kind":"text"}},"bytes":[2]}));
    expected.push(serde_json::json!({"error":"invalid_data"}));
    inputs.push(serde_json::json!({"type":{"kind":"text"},"bytes":[2,0,0,0,65]}));
    expected.push(serde_json::json!({"error":"invalid_data"}));
    let dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../target/bern-test/native-codec");
    fs::create_dir_all(&dir).unwrap();
    for f in native_files(&compiled.app) {
        let p = dir.join(f.path);
        fs::create_dir_all(p.parent().unwrap()).unwrap();
        fs::write(p, f.contents).unwrap();
    }
    let source = r#"
#define BERN_SWIFTUI_HOST 1
#include "Sources/BernNative.m"
int main(void) { @autoreleasepool {
    BNHost *host=[BNHost new];BNControl *unmounted=[host registerControl:@{@"id":@"probe",@"props":@{}} view:nil role:@"button" label:@"Probe" locals:@{@"__component":@"main",@"__keys":@""}];if(![unmounted.target isEqual:@"main.probe"])return 3;NSView *mounted=[NSView new];unmounted.view=mounted;if(objc_getAssociatedObject(mounted,@selector(registerControl:view:role:label:locals:))!=unmounted)return 4;NSData *input=[[NSFileHandle fileHandleWithStandardInput]readDataToEndOfFile];NSArray *cases=[NSJSONSerialization JSONObjectWithData:input options:0 error:nil];NSMutableArray *results=[NSMutableArray array];
    for(NSDictionary *entry in cases) { @try {
        NSMutableData *bytes=[NSMutableData data];for(NSNumber *number in entry[@"bytes"]){uint8_t byte=number.unsignedCharValue;[bytes appendBytes:&byte length:1];}
        BNReader *reader=[[BNReader alloc]initWithData:bytes];id value=[host decode:entry[@"type"] reader:reader];if(reader.position!=bytes.length)BNThrow(@"trailing_bytes",@"Unexpected bytes");BNWriter *writer=[BNWriter new];[host encode:value type:entry[@"type"] writer:writer];NSMutableArray *encoded=[NSMutableArray array];const uint8_t *ptr=writer.data.bytes;for(NSUInteger index=0;index<writer.data.length;index++)[encoded addObject:@(ptr[index])];[results addObject:@{@"value":value,@"bytes":encoded}];
    } @catch(NSException *error) {[results addObject:@{@"error":error.name}];}}
    NSData *output=[NSJSONSerialization dataWithJSONObject:results options:0 error:nil];[[NSFileHandle fileHandleWithStandardOutput]writeData:output];return 0;
} }
"#;
    fs::write(dir.join("Codec.m"), source).unwrap();
    let binary = dir.join("native-codec");
    let mut command = Command::new("xcrun");
    command.args([
        "--sdk",
        "macosx",
        "clang",
        "-fobjc-arc",
        "-fblocks",
        "-Wl,-undefined,dynamic_lookup",
    ]);
    for framework in [
        "AppKit",
        "Foundation",
        "QuartzCore",
        "AVFoundation",
        "CoreMedia",
        "CoreVideo",
        "UniformTypeIdentifiers",
    ] {
        command.args(["-framework", framework]);
    }
    let output = command
        .arg(dir.join("Codec.m"))
        .arg("-o")
        .arg(&binary)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "native codec compile: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let mut child = Command::new(binary)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(&serde_json::to_vec(&inputs).unwrap())
        .unwrap();
    let output = child.wait_with_output().unwrap();
    assert!(
        output.status.success(),
        "native codec run: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let result: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(result, serde_json::json!(expected));
}

#[cfg(target_os = "macos")]
#[test]
fn swift_host_uses_only_baseline_apis_and_swift_five_language_mode() {
    use std::{fs, process::Command};
    let (config, compiled) = project();
    for (platform, sdk, triple) in [
        (Platform::Macos, "macosx", "arm64-apple-macos11.0"),
        (
            Platform::Ios,
            "iphonesimulator",
            "arm64-apple-ios14.0-simulator",
        ),
        (Platform::Ios, "iphoneos", "arm64-apple-ios14.0"),
    ] {
        let mut context = context(
            &config,
            &compiled,
            if platform == Platform::Macos {
                "macos"
            } else {
                "ios"
            },
        );
        context.output_dir = context.output_dir.join(format!("swift-{sdk}"));
        for file in NativeTarget::new(platform, Frontend::SwiftUi)
            .generate(&compiled.app, &context)
            .unwrap()
        {
            let path = context.output_dir.join(file.path);
            fs::create_dir_all(path.parent().unwrap()).unwrap();
            fs::write(path, file.contents).unwrap();
        }
        let sdk_path = Command::new("xcrun")
            .args(["--sdk", sdk, "--show-sdk-path"])
            .output()
            .unwrap();
        assert!(sdk_path.status.success());
        let sdk_path = String::from_utf8(sdk_path.stdout).unwrap();
        let output = Command::new("xcrun")
            .args([
                "--sdk",
                sdk,
                "swiftc",
                "-swift-version",
                "5",
                "-parse-as-library",
                "-typecheck",
                "-target",
                triple,
                "-sdk",
                sdk_path.trim(),
                "-import-objc-header",
            ])
            .arg(context.output_dir.join("Sources/BernNative.h"))
            .arg(context.output_dir.join("Sources/BernHost.swift"))
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "Swift5 host {triple}: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
}

#[test]
fn mac_distribution_plan_preserves_helpers_signing_and_notarization_contract() {
    use bern_target_api::Signing;
    let (config, compiled) = project();
    let mut context = context(&config, &compiled, "macos");
    context.target.channels = vec!["ipc".into()];
    for frontend in [Frontend::ObjectiveC, Frontend::SwiftUi] {
        let target = NativeTarget::new(Platform::Macos, frontend);
        let plan = target
            .package(&compiled.app, &context, &Signing::default())
            .unwrap();
        assert!(
            plan.products
                .iter()
                .any(|p| p.extension().is_some_and(|e| e == "dmg"))
        );
        assert!(
            plan.steps.iter().any(
                |s| matches!(s,BuildStep::Copy{to,..}if to.ends_with("Contents/Helpers/hello"))
            )
        );
        assert!(plan.steps.iter().any(
            |s| matches!(s,BuildStep::Copy{to,..}if to.ends_with("Contents/Helpers/hello-mcp"))
        ));
        assert!(plan.steps.iter().any(|s|matches!(s,BuildStep::Write{path,..}if path.to_string_lossy().contains("Contents/Resources/skills/"))));
        assert!(
            !plan
                .steps
                .iter()
                .any(|s| matches!(s,BuildStep::Run{args,..}if args.iter().any(|a|a=="notarytool")))
        );
        let invalid = Signing {
            macos_notary_profile: Some("profile".into()),
            ..Default::default()
        };
        assert!(target.package(&compiled.app, &context, &invalid).is_err());
        let signed = Signing {
            macos_identity: Some("Developer ID Application: Example".into()),
            macos_notary_profile: Some("profile".into()),
            ..Default::default()
        };
        let plan = target.package(&compiled.app, &context, &signed).unwrap();
        assert!(
            plan.steps
                .iter()
                .any(|s| matches!(s,BuildStep::Run{args,..}if args.iter().any(|a|a=="notarytool")))
        );
        assert!(
            plan.steps
                .iter()
                .any(|s| matches!(s,BuildStep::Run{args,..}if args.iter().any(|a|a=="stapler")))
        );
        let build = target.plan(&compiled.app, &context).unwrap();
        assert!(build.products.iter().any(|p| p.ends_with("bin/hello")));
        assert!(
            build
                .products
                .iter()
                .any(|p| p.extension().is_some_and(|e| e == "dSYM"))
        );
        assert!(
            build
                .products
                .iter()
                .any(|p| p.file_name().is_some_and(|n| n == "SKILL.md"))
        );
    }
}
