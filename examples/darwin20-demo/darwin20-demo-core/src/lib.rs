//! The engine of Darwin20 Demo: the business logic, in plain Rust. It knows
//! nothing about windows, so it is tested without one.

use bern::CommandError;
use darwin20_demo_protocol::darwin20_demo::{self, State};

pub struct Darwin20DemoEngine {
    state: State,
}

impl Default for Darwin20DemoEngine {
    fn default() -> Self {
        Self {
            state: State { count: 0 },
        }
    }
}

impl darwin20_demo::Commands for Darwin20DemoEngine {
    fn add_one(&mut self) -> Result<(), CommandError> {
        self.state.count += 1;
        Ok(())
    }

    fn reset(&mut self) -> Result<(), CommandError> {
        self.state.count = 0;
        Ok(())
    }
}

impl darwin20_demo::Engine for Darwin20DemoEngine {
    fn state(&self) -> &State {
        &self.state
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use darwin20_demo::Commands;

    #[test]
    fn the_button_counts_and_reset_starts_over() {
        let mut engine = Darwin20DemoEngine::default();
        engine.add_one().unwrap();
        engine.add_one().unwrap();
        assert_eq!(engine.state.count, 2);
        engine.reset().unwrap();
        assert_eq!(engine.state.count, 0);
    }
}
