// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract AlertLogger {
    struct Alert {
        string alertType;   // Example: "DROWSY", "DISTRACTED", "NO_FACE"
        uint256 timestamp;  // When alert happened
    }

    struct DriverLog {
        uint256 totalAlerts;
        Alert[] alerts;
    }

    mapping(string => DriverLog) private driverLogs;

    // Log an alert for a given driverId
    function logAlert(string memory driverId, string memory alertType) public {
        driverLogs[driverId].alerts.push(Alert(alertType, block.timestamp));
        driverLogs[driverId].totalAlerts++;
    }

    // Get total alerts for a driver
    function getTotalAlerts(string memory driverId) public view returns (uint256) {
        return driverLogs[driverId].totalAlerts;
    }

    // Get all alerts for a driver
    function getAlerts(string memory driverId) public view returns (Alert[] memory) {
        return driverLogs[driverId].alerts;
    }
}
