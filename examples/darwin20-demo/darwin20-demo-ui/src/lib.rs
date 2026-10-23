//! The interface of Darwin20 Demo: one window with a counter. Every string is
//! written in every language next to where it is shown, and every button
//! runs a command from the protocol.

use bern::prelude::*;
use darwin20_demo_protocol::darwin20_demo;

#[component]
pub fn app(app: darwin20_demo::Client, windows: AppWindows) -> impl View {
    ui! {
        WindowSet(handle: AppWindows, primary: main) {
            Window(id: main, title: tr! { "zh-Hans" => "Darwin20 Demo", "en" => "Darwin20 Demo" }, initial: open, width: 480, height: 320) {
                Column(gap: 16, padding: 24, align: center) {
                    Text(content: tr! { "zh-Hans" => "你好，世界！", "en" => "Hello, World!" }, style: title)
                    Text(content: tr! { "zh-Hans" => "按钮按下次数：{count}", "en" => "Button presses: {count}"; count: app.count })
                    Row(gap: 12) {
                        Button(id: add_one, label: tr! { "zh-Hans" => "加一", "en" => "Add One" }, prominence: prominent) => app.add_one()
                        Button(id: reset, label: tr! { "zh-Hans" => "重置", "en" => "Reset" }) => app.reset()
                    }
                    // Modules added with `bern new --module` show here.
                    Slot(id: extras)
                }
            }
        }
    }
}
