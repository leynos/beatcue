Feature: Architecture package skeleton

  Scenario: The production package exposes the hexagonal boundary
    Given the BeatCue package skeleton is installed
    When the architecture checker runs against the production package
    Then the domain, application, adapter, and config packages are classified
    And the architecture checker reports no production boundary violations
