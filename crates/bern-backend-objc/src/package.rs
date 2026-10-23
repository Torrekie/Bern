//! macOS distribution plan using the same bundle/CLI/notarization contract as
//! the modern Apple backend. This creates a plan; it never publishes a package.
use crate::product_name;
use bern_ir::Application;
use bern_target_api::{
    BuildContext, BuildPlan, BuildStep, Diagnostic, Signing, dist_dir, package_architecture, skill,
};

pub fn macos(
    app: &Application,
    context: &BuildContext,
    signing: &Signing,
) -> Result<BuildPlan, Vec<Diagnostic>> {
    let product = product_name(app);
    let output = &context.output_dir;
    let cli = app.app.id.replace('_', "-");
    let stage = output.join("package");
    let volume = stage.join("volume");
    let staged = volume.join(format!("{product}.app"));
    let helpers = staged.join("Contents/Helpers");
    let dist = dist_dir(context);
    let image = dist.join(format!(
        "{product}-{}-macos-{}.dmg",
        app.app.version,
        package_architecture()
    ));
    let name = app
        .app
        .name
        .get(&app.languages.default)
        .map(str::to_string)
        .unwrap_or_else(|| product.clone());
    if signing.macos_notary_profile.is_some() && signing.macos_identity.is_none() {
        return Err(vec![Diagnostic::error(
            "BERN_MACOS_NOTARY_PROFILE needs BERN_MACOS_SIGNING_IDENTITY: notarization takes a Developer ID signature",
        )]);
    }
    let run = |description: &str, program: &str, args: Vec<String>| BuildStep::Run {
        description: description.into(),
        program: program.into(),
        args,
        cwd: output.clone(),
        env: vec![],
    };
    let path = |path: &std::path::Path| path.display().to_string();
    // Hardened runtime and a timestamp with a real identity; an ad hoc
    // signature otherwise.
    let sign = |target: &std::path::Path| -> Vec<String> {
        match &signing.macos_identity {
            Some(identity) => vec![
                "--force".into(),
                "--options".into(),
                "runtime".into(),
                "--timestamp".into(),
                "--sign".into(),
                identity.clone(),
                path(target),
            ],
            None => vec!["--force".into(), "--sign".into(), "-".into(), path(target)],
        }
    };
    let mut steps = vec![
        BuildStep::RemoveIfExists {
            path: stage.clone(),
        },
        BuildStep::CreateDir {
            path: volume.clone(),
        },
        BuildStep::CreateDir { path: dist.clone() },
        BuildStep::RemoveIfExists {
            path: image.clone(),
        },
        run(
            "Copy the app",
            "ditto",
            vec![path(&output.join(format!("{product}.app"))), path(&staged)],
        ),
        BuildStep::CreateDir {
            path: helpers.clone(),
        },
    ];
    for program in [cli.clone(), format!("{cli}-mcp")] {
        steps.push(BuildStep::Copy {
            from: output.join("bin").join(&program),
            to: helpers.join(&program),
        });
        steps.push(run(
            "Sign the command line tools",
            "codesign",
            sign(&helpers.join(&program)),
        ));
    }
    // The agent skill goes with the resources, which the signature
    // seals; it finds the programs in `Helpers`.
    if skill::listens(&context.target.channels) {
        let place = skill::Place {
            cli: format!("../../../Helpers/{cli}"),
            mcp: format!("../../../Helpers/{cli}-mcp"),
            installed: Some(format!(
                "/Applications/{product}.app/Contents/Helpers/{cli}"
            )),
            connect: None,
        };
        steps.push(BuildStep::Write {
            path: staged.join("Contents/Resources").join(skill::path(app)),
            contents: skill::markdown(app, &place).into_bytes(),
        });
    }
    steps.push(run("Sign the app", "codesign", sign(&staged)));
    steps.push(run(
        "Link Applications",
        "ln",
        vec![
            "-s".into(),
            "/Applications".into(),
            path(&volume.join("Applications")),
        ],
    ));
    // `diskutil image` where macOS has it; `hdiutil create`, which newer
    // systems call deprecated, before that.
    let diskutil = std::process::Command::new("diskutil")
        .args(["image", "create", "from", "--help"])
        .output()
        .is_ok_and(|output| output.status.success());
    steps.push(if diskutil {
        run(
            "Make the disk image",
            "diskutil",
            vec![
                "image".into(),
                "create".into(),
                "from".into(),
                "--format".into(),
                "UDZO".into(),
                "--volumeName".into(),
                name,
                path(&volume),
                path(&image),
            ],
        )
    } else {
        run(
            "Make the disk image",
            "hdiutil",
            vec![
                "create".into(),
                "-volname".into(),
                name,
                "-srcfolder".into(),
                path(&volume),
                "-ov".into(),
                "-format".into(),
                "UDZO".into(),
                path(&image),
            ],
        )
    });
    let mut notes = Vec::new();
    match (&signing.macos_identity, &signing.macos_notary_profile) {
        (Some(identity), profile) => {
            steps.push(run(
                "Sign the disk image",
                "codesign",
                vec![
                    "--force".into(),
                    "--timestamp".into(),
                    "--sign".into(),
                    identity.clone(),
                    path(&image),
                ],
            ));
            if let Some(profile) = profile {
                steps.push(run(
                    "Notarize the disk image",
                    "xcrun",
                    vec![
                        "notarytool".into(),
                        "submit".into(),
                        path(&image),
                        "--keychain-profile".into(),
                        profile.clone(),
                        "--wait".into(),
                    ],
                ));
                steps.push(run(
                    "Staple the notarization",
                    "xcrun",
                    vec!["stapler".into(), "staple".into(), path(&image)],
                ));
            } else {
                notes.push(
                    "the disk image is signed but not notarized; Gatekeeper on other Macs warns about it (set BERN_MACOS_NOTARY_PROFILE)"
                        .into(),
                );
            }
        }
        (None, _) => notes.push(
            "the app is signed for this Mac only; Gatekeeper on other Macs refuses it (set BERN_MACOS_SIGNING_IDENTITY to a Developer ID Application identity)"
                .into(),
        ),
    }
    Ok(BuildPlan {
        steps,
        products: vec![image],
        run: None,
        notes,
    })
}
