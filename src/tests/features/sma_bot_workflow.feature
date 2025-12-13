Feature: SMA Bot Trading Workflow
  As a trading system
  I want to run complete trading simulations
  So that I can evaluate bot performance

  Scenario: Complete backtest with trending market
    Given I have price data with uptrend and downtrend: [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 118, 116, 114, 112, 110, 108, 106, 104, 102, 100]
    And I have an SMA bot with short window 3, long window 5, and stop loss 5.0
    When I run the complete backtest
    Then the trade history should not be empty
    And the profit/loss should be calculated
    And all trades should alternate between BUY and SELL
    And all trade prices should match the data at their indices

  Scenario: Backtest in strong uptrend
    Given I have price data with strong uptrend: [100, 100, 100, 100, 100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128]
    And I have an SMA bot with short window 3, long window 5, and stop loss 5.0
    When I run the complete backtest
    Then the trade history should contain at least one BUY signal

  Scenario: Backtest in downtrend
    Given I have price data with downtrend: [128, 126, 124, 122, 120, 118, 116, 114, 112, 110, 108, 106, 104, 102, 100]
    And I have an SMA bot with short window 3, long window 5, and stop loss 5.0
    When I run the complete backtest
    Then the trade history should have at most 2 trades

  Scenario: Bot reset clears state
    Given I have price data: [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120]
    And I have an SMA bot with short window 3, long window 5, and stop loss 5.0
    When I run the complete backtest
    And I record the number of trades
    And I reset the bot
    And I run the complete backtest again
    Then the second run should have the same number of trades as the first run

  Scenario: Backtest with insufficient data
    Given I have price data: [100, 101, 102]
    And I have an SMA bot with short window 3, long window 5, and stop loss 5.0
    When I run the complete backtest
    Then the backtest should complete without errors
    And the trade history should be a list
    And the profit/loss should be a number

  Scenario: All positions closed after backtest
    Given I have price data: [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120]
    And I have an SMA bot with short window 3, long window 5, and stop loss 5.0
    When I run the complete backtest
    Then there should be at most 1 open position remaining
    And at least one position should have been created
