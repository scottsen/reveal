/// A simple calculator library demonstrating Rust features
/// Showcases structs, enums, traits, and error handling

use std::fmt;
use std::ops::{Add, Sub, Mul, Div};

/// Represents a calculation result
pub type Result<T> = std::result::Result<T, CalcError>;

/// Custom error type for calculator operations
#[derive(Debug, Clone, PartialEq)]
pub enum CalcError {
    DivisionByZero,
    Overflow,
    InvalidOperation(String),
}

impl fmt::Display for CalcError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            CalcError::DivisionByZero => write!(f, "Division by zero"),
            CalcError::Overflow => write!(f, "Numeric overflow"),
            CalcError::InvalidOperation(msg) => write!(f, "Invalid operation: {}", msg),
        }
    }
}

impl std::error::Error for CalcError {}

/// Main calculator struct
#[derive(Debug, Clone, Copy)]
pub struct Calculator {
    /// Current accumulated value
    pub value: f64,
    /// Precision for floating point comparisons
    precision: u32,
}

impl Calculator {
    /// Create a new calculator with initial value
    pub fn new(initial: f64) -> Self {
        Self {
            value: initial,
            precision: 6,
        }
    }

    /// Create calculator with zero initial value
    pub fn zero() -> Self {
        Self::new(0.0)
    }

    /// Add a value to the calculator
    pub fn add(&mut self, x: f64) -> &mut Self {
        self.value += x;
        self
    }

    /// Subtract a value from the calculator
    pub fn sub(&mut self, x: f64) -> &mut Self {
        self.value -= x;
        self
    }

    /// Multiply the current value
    pub fn mul(&mut self, x: f64) -> &mut Self {
        self.value *= x;
        self
    }

    /// Divide the current value
    pub fn div(&mut self, x: f64) -> Result<&mut Self> {
        if x == 0.0 {
            return Err(CalcError::DivisionByZero);
        }
        self.value /= x;
        Ok(self)
    }

    /// Get the current value
    pub fn get(&self) -> f64 {
        self.value
    }

    /// Reset calculator to zero
    pub fn reset(&mut self) {
        self.value = 0.0;
    }

    /// Set the precision for operations
    pub fn set_precision(&mut self, precision: u32) {
        self.precision = precision;
    }
}

impl Default for Calculator {
    fn default() -> Self {
        Self::zero()
    }
}

/// Trait for types that can be calculated
pub trait Calculable {
    fn calculate(&self) -> f64;
}

impl Calculable for Calculator {
    fn calculate(&self) -> f64 {
        self.value
    }
}

/// Operations that can be performed
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Operation {
    Add,
    Subtract,
    Multiply,
    Divide,
}

impl Operation {
    /// Apply this operation to two values
    pub fn apply(&self, left: f64, right: f64) -> Result<f64> {
        match self {
            Operation::Add => Ok(left + right),
            Operation::Subtract => Ok(left - right),
            Operation::Multiply => Ok(left * right),
            Operation::Divide => {
                if right == 0.0 {
                    Err(CalcError::DivisionByZero)
                } else {
                    Ok(left / right)
                }
            }
        }
    }
}

/// A more advanced scientific calculator
pub struct ScientificCalc {
    base: Calculator,
    history: Vec<f64>,
}

impl ScientificCalc {
    /// Create new scientific calculator
    pub fn new() -> Self {
        Self {
            base: Calculator::zero(),
            history: Vec::new(),
        }
    }

    /// Calculate power
    pub fn pow(&mut self, exponent: f64) -> &mut Self {
        self.base.value = self.base.value.powf(exponent);
        self.history.push(self.base.value);
        self
    }

    /// Calculate square root
    pub fn sqrt(&mut self) -> Result<&mut Self> {
        if self.base.value < 0.0 {
            return Err(CalcError::InvalidOperation("Cannot sqrt negative".to_string()));
        }
        self.base.value = self.base.value.sqrt();
        self.history.push(self.base.value);
        Ok(self)
    }

    /// Get calculation history
    pub fn history(&self) -> &[f64] {
        &self.history
    }

    /// Clear history
    pub fn clear_history(&mut self) {
        self.history.clear();
    }
}

impl Default for ScientificCalc {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_operations() {
        let mut calc = Calculator::zero();
        calc.add(5.0).mul(2.0).sub(3.0);
        assert_eq!(calc.get(), 7.0);
    }

    #[test]
    fn test_division_by_zero() {
        let mut calc = Calculator::new(10.0);
        let result = calc.div(0.0);
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), CalcError::DivisionByZero);
    }

    #[test]
    fn test_scientific_calc() {
        let mut calc = ScientificCalc::new();
        calc.base.value = 4.0;
        calc.sqrt().unwrap();
        assert_eq!(calc.base.value, 2.0);
    }
}
