Feature: SMA Bot Initialization
  As a trading system
  I want to initialize an SMA bot with proper configuration
  So that the bot can trade with correct parameters

  Scenario: Initialize bot with default parameters
    Given I have price data with timeframe "ONEDAY"
    When I create an SMA bot with name "TestBot" and default parameters
    Then the bot should have short window of 40
    And the bot should have long window of 100
    And the bot should have stop loss percent of 5.0
    And the bot should have amount of 1.0
    And the bot should have no open positions
    And the bot should have empty trade history

  Scenario: Initialize bot with custom parameters
    Given I have price data with timeframe "ONEDAY"
    When I create an SMA bot with name "CustomBot", short window 20, long window 50, stop loss 7.5, and amount 2.5
    Then the bot should have short window of 20
    And the bot should have long window of 50
    And the bot should have stop loss percent of 7.5
    And the bot should have amount of 2.5

  Scenario: Reject invalid window configuration
    Given I have price data with timeframe "ONEDAY"
    When I try to create an SMA bot with short window 100 and long window 50
    Then the bot creation should fail with error "short_window must be less than long_window"

  Scenario: Reject zero window size
    Given I have price data with timeframe "ONEDAY"
    When I try to create an SMA bot with short window 0 and long window 50
    Then the bot creation should fail with error "window sizes must be positive"

  Scenario: Reject negative stop loss
    Given I have price data with timeframe "ONEDAY"
    When I try to create an SMA bot with stop loss percent -5.0
    Then the bot creation should fail with error "stop_loss_percent must be positive"

  Scenario: Reject zero amount
    Given I have price data with timeframe "ONEDAY"
    When I try to create an SMA bot with amount 0
    Then the bot creation should fail with error "amount must be positive"
