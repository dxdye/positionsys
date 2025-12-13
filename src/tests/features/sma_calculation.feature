Feature: SMA Calculation
  As a trading bot
  I want to calculate Simple Moving Averages accurately
  So that I can make correct trading decisions

  Scenario: Calculate SMA with sufficient data
    Given I have an SMA bot
    And I have price data: [100, 102, 101, 103, 105]
    When I calculate SMA with window size 3
    Then the SMA should be approximately 103.0

  Scenario: Calculate SMA with insufficient data
    Given I have an SMA bot
    And I have price data: [100, 102]
    When I calculate SMA with window size 3
    Then the SMA should be None

  Scenario: Calculate SMA with exact window size
    Given I have an SMA bot
    And I have price data: [100, 102, 101]
    When I calculate SMA with window size 3
    Then the SMA should be approximately 101.0

  Scenario: Calculate SMA with empty list
    Given I have an SMA bot
    And I have an empty price list
    When I calculate SMA with window size 3
    Then the SMA should be None

  Scenario: Calculate SMA with window of one
    Given I have an SMA bot
    And I have price data: [100, 102, 101, 103, 105]
    When I calculate SMA with window size 1
    Then the SMA should be 105.0

  Scenario: SMA uses latest prices
    Given I have an SMA bot
    And I have price data: [100, 101, 102, 103, 104, 105, 106]
    When I calculate SMA with window size 3
    Then the SMA should be approximately 105.0
