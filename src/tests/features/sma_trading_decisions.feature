Feature: SMA Trading Decisions
  As a trading bot
  I want to make correct trading decisions based on SMA crossovers
  So that I can execute profitable trades

  Background:
    Given I have an SMA bot with short window 3 and long window 5

  Scenario: Hold when insufficient data
    Given I have price data: [100, 101, 102]
    When I call decide_and_trade at index 2
    Then the decision should be "HOLD"

  Scenario: Generate BUY signal on golden cross
    Given I have price data: [100, 102, 104, 106, 108, 110, 112]
    When I call decide_and_trade at index 6
    Then the decision should be "BUY"
    And the bot should have 1 open position
    And the position should be a StopLossPosition

  Scenario: No second BUY when already in position
    Given I have price data: [100, 102, 104, 106, 108, 110, 112, 114, 116]
    And I have opened a position at index 6
    When I call decide_and_trade at index 8
    Then the decision should be "HOLD"
    And the bot should have 1 position

  Scenario: Generate SELL signal on death cross
    Given I have price data: [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]
    And I have opened a position at index 7
    When I call decide_and_trade at index 12
    Then the decision should be "SELL"
    And the bot should have no open positions

  Scenario: No SELL when not in position
    Given I have price data: [100, 102, 101, 103, 105, 104, 110, 112, 115, 114, 112, 110, 108]
    When I call decide_and_trade at index 12
    Then the decision should be "HOLD"
    And the bot should have no open positions
