//! Shared Apple document registration for every native frontend.
use bern_ir::Application;

fn xml(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

/// The kinds of file the application opens: those of every `Drop` with
/// `opens: true`, in components and in the content written directly in a
/// window, each once, in a stable order.
fn opened_kinds(app: &Application) -> Vec<String> {
    let mut kinds = std::collections::BTreeSet::new();
    app.walk(&mut |node, _| {
        if let bern_ir::Node::Element(element) = node
            && element.kind == "Drop"
            && element.keyword("opens") == Some("true")
        {
            for word in element.keyword("files").unwrap_or("any").split(' ') {
                kinds.insert(word.to_string());
            }
        }
    });
    kinds.into_iter().collect()
}

/// `CFBundleDocumentTypes` for the kinds the application opens, so the
/// system offers it under "Open With" without making it the default. On
/// macOS extensions the system may not know are listed as extensions; iOS
/// only takes types, so it imports one for each and opens files in place.
pub fn document_types(app: &Application, ios: bool) -> String {
    document_entries(&opened_kinds(app), &app.app.bundle_id, ios)
}

pub fn document_entries(kinds: &[String], bundle_id: &str, ios: bool) -> String {
    if kinds.is_empty() {
        return String::new();
    }
    let system_type = |kind: &str| match kind {
        "video" => "public.movie",
        "audio" => "public.audio",
        "picture" => "public.image",
        "folder" => "public.folder",
        _ => "public.item",
    };
    let imported = |ext: &str| format!("{bundle_id}.file.{ext}");
    // The names Finder shows in an app's document types.
    let title = |kind: &str| match kind.strip_prefix('.') {
        Some(ext) => format!("{} File", ext.to_uppercase()),
        None => match kind {
            "video" => "Video".into(),
            "audio" => "Audio".into(),
            "picture" => "Picture".into(),
            "folder" => "Folder".into(),
            _ => "File".into(),
        },
    };
    let strings = |values: &[String]| -> String {
        values
            .iter()
            .map(|value| format!("\n                <string>{}</string>", xml(value)))
            .collect()
    };
    let mut entries = Vec::new();
    let mut declarations = Vec::new();
    let mut entry = |name: &str, key: &str, values: &[String]| {
        entries.push(format!(
            r#"
        <dict>
            <key>CFBundleTypeName</key>
            <string>{name}</string>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
            <key>LSHandlerRank</key>
            <string>Alternate</string>
            <key>{key}</key>
            <array>{}
            </array>
        </dict>"#,
            strings(values)
        ))
    };
    for kind in kinds {
        let (extensions, conforms): (Vec<String>, &str) = match kind.strip_prefix('.') {
            Some(ext) => (vec![ext.to_string()], "public.data"),
            None => (
                bern_ir::spec::file_kind_extensions(kind)
                    .iter()
                    .map(|ext| (*ext).to_string())
                    .collect(),
                system_type(kind),
            ),
        };
        let mut types = Vec::new();
        if !kind.starts_with('.') {
            types.push(system_type(kind).to_string());
        }
        if ios {
            for ext in &extensions {
                types.push(imported(ext));
                declarations.push(format!(
                    r#"
        <dict>
            <key>UTTypeIdentifier</key>
            <string>{}</string>
            <key>UTTypeDescription</key>
            <string>{}</string>
            <key>UTTypeConformsTo</key>
            <array>
                <string>{conforms}</string>
            </array>
            <key>UTTypeTagSpecification</key>
            <dict>
                <key>public.filename-extension</key>
                <array>
                    <string>{}</string>
                </array>
            </dict>
        </dict>"#,
                    xml(&imported(ext)),
                    xml(&ext.to_uppercase()),
                    xml(ext)
                ));
            }
            entry(&title(kind), "LSItemContentTypes", &types);
        } else {
            if !types.is_empty() {
                entry(&title(kind), "LSItemContentTypes", &types);
            }
            if !extensions.is_empty() {
                entry(&title(kind), "CFBundleTypeExtensions", &extensions);
            }
        }
    }
    let mut out = format!(
        "\n    <key>CFBundleDocumentTypes</key>\n    <array>{}\n    </array>",
        entries.concat()
    );
    if ios {
        out.push_str(&format!(
            "\n    <key>UTImportedTypeDeclarations</key>\n    <array>{}\n    </array>\n    <key>LSSupportsOpeningDocumentsInPlace</key>\n    <true/>",
            declarations.concat()
        ));
    }
    out
}
