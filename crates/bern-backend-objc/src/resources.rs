//! Reuse Bern's icon inputs and localization tables in both Apple host modes.
use crate::{MINIMUM_IOS, Platform};
use bern_ir::Application;
use bern_target_api::{BuildContext, BuildStep, Diagnostic, GeneratedFile, icon};
use std::path::{Path, PathBuf};

const ASSETS: &str = "Assets.xcassets";
const ICON: &str = "AppIcon";

fn escaped(s: &str) -> String {
    s.replace('\\', "\\\\")
        .replace('"', "\\\"")
        .replace('\n', "\\n")
        .replace('\r', "\\r")
        .replace('\t', "\\t")
}

fn slots() -> Vec<(&'static str, &'static str, u32, u32)> {
    let mut result = vec![];
    for (points, base) in [("20x20", 20), ("29x29", 29), ("40x40", 40), ("60x60", 60)] {
        for scale in [2, 3] {
            result.push(("iphone", points, scale, base * scale));
        }
    }
    for (points, base) in [("20x20", 20), ("29x29", 29), ("40x40", 40), ("76x76", 76)] {
        for scale in [1, 2] {
            result.push(("ipad", points, scale, base * scale));
        }
    }
    result.push(("ipad", "83.5x83.5", 2, 167));
    result.push(("ios-marketing", "1024x1024", 1, 1024));
    result
}

fn legacy_icon_name(size: &str, scale: u32) -> String {
    let points = size.split('x').next().unwrap();
    format!(
        "BernIcon-{points}{}.png",
        if scale == 1 {
            String::new()
        } else {
            format!("@{scale}x")
        }
    )
}

pub fn files(
    app: &Application,
    context: &BuildContext,
    platform: Platform,
    bundle: &Path,
) -> Result<Vec<GeneratedFile>, Vec<Diagnostic>> {
    let fail = |message: String| vec![Diagnostic::error(message)];
    let resources = if platform == Platform::Macos {
        bundle.join("Contents/Resources")
    } else {
        bundle.to_path_buf()
    };
    let mut files = vec![];
    for language in &app.languages.supported {
        let name =
            bern_target_api::texts::translation(&app.app.name, language, &app.languages.default);
        files.push(GeneratedFile::text(
            resources.join(format!("{language}.lproj/InfoPlist.strings")),
            format!(
                "CFBundleName = \"{}\";\nCFBundleDisplayName = \"{}\";\n",
                escaped(name),
                escaped(name)
            ),
        ));
    }
    if platform == Platform::Macos {
        let contents = match icon::source(app, "macos", &context.project_dir) {
            icon::Source::Native(path) => std::fs::read(&path)
                .map_err(|error| fail(format!("cannot read icon {}: {error}", path.display())))?,
            _ => icon::icns(
                &icon::images(app, "macos", &context.project_dir, icon::Shape::Masked)
                    .map_err(fail)?,
            ),
        };
        files.push(GeneratedFile {
            path: resources.join("AppIcon.icns"),
            contents,
        });
    } else {
        let set = PathBuf::from(ASSETS).join(format!("{ICON}.appiconset"));
        files.push(GeneratedFile::text(
            PathBuf::from(ASSETS).join("Contents.json"),
            "{\"info\":{\"author\":\"bern\",\"version\":1}}\n",
        ));
        if let icon::Source::Native(directory) = icon::source(app, "ios", &context.project_dir) {
            for relative in icon::app_icon_set(&directory).map_err(fail)? {
                let contents = std::fs::read(directory.join(&relative)).map_err(|error| {
                    fail(format!(
                        "cannot read icon {}: {error}",
                        directory.join(&relative).display()
                    ))
                })?;
                files.push(GeneratedFile {
                    path: set.join(relative),
                    contents,
                });
            }
        } else {
            let images = icon::images(app, "ios", &context.project_dir, icon::Shape::Masked)
                .map_err(fail)?;
            files.push(GeneratedFile {
                path: PathBuf::from(ASSETS).join("BernIconSource.png"),
                contents: icon::largest(&images).png.to_vec(),
            });
            let images=slots().into_iter().map(|(idiom,size,scale,pixels)|serde_json::json!({"idiom":idiom,"size":size,"scale":format!("{scale}x"),"filename":format!("Icon-{pixels}.png")})).collect::<Vec<_>>();
            files.push(GeneratedFile::text(
                set.join("Contents.json"),
                serde_json::to_string_pretty(
                    &serde_json::json!({"images":images,"info":{"author":"bern","version":1}}),
                )
                .unwrap(),
            ));
        }
    }
    Ok(files)
}

pub fn keep(app: &Application, platform: Platform) -> Vec<PathBuf> {
    let mut paths = app
        .languages
        .supported
        .iter()
        .map(|language| PathBuf::from(format!("{language}.lproj/InfoPlist.strings")))
        .collect::<Vec<_>>();
    paths.push(
        if platform == Platform::Macos {
            "AppIcon.icns"
        } else {
            "Info.plist"
        }
        .into(),
    );
    if platform == Platform::Ios {
        paths.extend(
            slots()
                .into_iter()
                .filter(|(idiom, _, _, _)| *idiom != "ios-marketing")
                .map(|(_, size, scale, _)| PathBuf::from(legacy_icon_name(size, scale))),
        );
    }
    paths
}

/// Raster icons use the system's legacy icon files contract. This is supported
/// at the deployment baseline and does not require a simulator to build a
/// device app. User-supplied asset catalogs retain the normal actool workflow.
pub fn icon_plist(app: &Application, context: &BuildContext) -> String {
    if matches!(
        icon::source(app, "ios", &context.project_dir),
        icon::Source::Native(_)
    ) {
        return "<key>CFBundleIcons</key><dict><key>CFBundlePrimaryIcon</key><dict><key>CFBundleIconName</key><string>AppIcon</string></dict></dict>\n".into();
    }
    let files = |device: &str| {
        slots()
            .into_iter()
            .filter(|(idiom, _, _, _)| *idiom == device)
            .map(|(_, size, _, _)| size.split('x').next().unwrap())
            .collect::<std::collections::BTreeSet<_>>()
            .into_iter()
            .map(|points| format!("<string>BernIcon-{points}</string>"))
            .collect::<String>()
    };
    format!(
        "<key>CFBundleIcons</key><dict><key>CFBundlePrimaryIcon</key><dict><key>CFBundleIconFiles</key><array>{}</array></dict></dict>\n<key>CFBundleIcons~ipad</key><dict><key>CFBundlePrimaryIcon</key><dict><key>CFBundleIconFiles</key><array>{}</array></dict></dict>\n",
        files("iphone"),
        files("ipad")
    )
}

pub fn steps(
    app: &Application,
    context: &BuildContext,
    platform: Platform,
    bundle: &Path,
) -> Result<Vec<BuildStep>, Vec<Diagnostic>> {
    if platform == Platform::Macos {
        return Ok(vec![]);
    }
    let output = &context.output_dir;
    let path = |p: &Path| p.display().to_string();
    let run = |description: &str, program: &str, args: Vec<String>| BuildStep::Run {
        description: description.into(),
        program: program.into(),
        args,
        cwd: output.clone(),
        env: vec![],
    };
    let mut steps = vec![];
    if !matches!(
        icon::source(app, "ios", &context.project_dir),
        icon::Source::Native(_)
    ) {
        let sizes = slots()
            .into_iter()
            .filter(|(idiom, _, _, _)| *idiom != "ios-marketing")
            .map(|(_, size, scale, pixels)| (legacy_icon_name(size, scale), pixels))
            .collect::<std::collections::BTreeSet<_>>();
        for (name, pixels) in sizes {
            steps.push(run(
                "Prepare a legacy iOS icon size",
                "sips",
                vec![
                    "-z".into(),
                    pixels.to_string(),
                    pixels.to_string(),
                    path(&output.join(ASSETS).join("BernIconSource.png")),
                    "--out".into(),
                    path(&bundle.join(name)),
                ],
            ));
        }
        return Ok(steps);
    }
    let sdk = if context.target.destination.as_deref() == Some("device") {
        "iphoneos"
    } else {
        "iphonesimulator"
    };
    steps.push(run(
        "Compile the iOS application icon",
        "xcrun",
        vec![
            "actool".into(),
            path(&output.join(ASSETS)),
            "--compile".into(),
            path(bundle),
            "--platform".into(),
            sdk.into(),
            "--minimum-deployment-target".into(),
            MINIMUM_IOS.into(),
            "--app-icon".into(),
            ICON.into(),
            "--output-partial-info-plist".into(),
            path(&output.join("AssetCatalog.plist")),
            "--target-device".into(),
            "iphone".into(),
            "--target-device".into(),
            "ipad".into(),
            "--output-format".into(),
            "human-readable-text".into(),
            "--errors".into(),
            "--warnings".into(),
        ],
    ));
    Ok(steps)
}

pub fn check(app: &Application, platform: Platform) -> Vec<Diagnostic> {
    let product = crate::product_name(app);
    app.resources
        .iter()
        .filter_map(|resource| {
            let parts = resource.name.split('/').collect::<Vec<_>>();
            let reserved = parts.iter().any(|part| part.ends_with(".lproj"))
                || (platform == Platform::Macos && resource.name == "AppIcon.icns")
                || (platform == Platform::Ios
                    && (parts[0] == product
                        || parts[0].starts_with("AppIcon")
                        || parts[0].starts_with("BernIcon-")
                        || [
                            "Info.plist",
                            "Assets.car",
                            "Frameworks",
                            "PlugIns",
                            "_CodeSignature",
                        ]
                        .contains(&parts[0])))
                || parts[..parts.len() - 1]
                    .iter()
                    .any(|part| part.contains('.'));
            reserved.then(|| {
                Diagnostic::error(format!(
                    "resource `{}` conflicts with the Apple app bundle layout; rename it",
                    resource.name
                ))
                .at(resource.declared.clone())
            })
        })
        .collect()
}
