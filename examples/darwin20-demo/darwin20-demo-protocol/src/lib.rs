//! The protocol of Darwin20 Demo: the state the interface shows, and the commands
//! that change it. The interface, the command line and the MCP server all go
//! through these commands.

#[bern::protocol(namespace = "darwin20_demo", version = 1)]
pub mod darwin20_demo {
    use bern::prelude::*;

    #[state]
    pub struct State {
        /// How many times the button was pressed.
        pub count: i64,
    }

    #[commands]
    pub trait Commands {
        /// Add one to the count.
        fn add_one(&mut self) -> Result<(), CommandError>;

        /// Count from zero again.
        fn reset(&mut self) -> Result<(), CommandError>;
    }
}
