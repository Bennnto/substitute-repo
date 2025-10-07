# CLI Assistant Test Suite

This directory contains a comprehensive test suite for the CLI Assistant application, including tests for the newly added network scanning and CCTV detection features.

## Test Files

### 1. `test_cli_assistant_comprehensive.py`
The main comprehensive test suite that tests all functions in `cli_assistant.py`:
- **SimpleMenu class tests**: Tests for menu navigation, dropdowns, confirmations, and input prompts
- **UltimateCronManager class tests**: Tests for all job management, file operations, security features, and network scanning
- **Integration tests**: End-to-end workflow tests
- **Network scanning tests**: Specific tests for the new camera detection features

### 2. `run_tests.py`
A user-friendly test runner that provides:
- Dependency checking
- Categorized test execution (basic, network, security, comprehensive)
- Interactive test selection
- Detailed reporting and summaries
- Test report generation

### 3. `test_network_functions.py`
A focused test script specifically for the network scanning features:
- Tests for `get_local_ip()`, `is_local_ip()`, `identify_camera_type()`
- Tests for camera scanning functions with mocked network responses
- Integration tests to ensure new features work with the main CLI

## Running the Tests

### Quick Network Function Test
```bash
python3 test_network_functions.py
```
This runs a focused test on just the network scanning features.

### Interactive Test Runner
```bash
python3 run_tests.py
```
This provides an interactive interface to run different categories of tests.

### Full Comprehensive Test Suite
```bash
python3 test_cli_assistant_comprehensive.py
```
This runs the complete test suite with all 100+ test cases.

## Test Categories

### 1. Basic Functionality Tests
- Module imports and initialization
- Configuration loading and saving
- Basic menu operations

### 2. Job Management Tests
- Job creation, editing, deletion
- Job validation and syntax checking
- Import/export functionality
- Backup and restore operations

### 3. File Management Tests
- File encryption/decryption
- File browser operations
- Directory synchronization
- Large file downloads

### 4. Security Tests
- Security scanning functions
- File permissions checking
- Firewall status verification
- Antivirus detection
- **NEW**: Network camera scanning
- **NEW**: CCTV detection

### 5. Network Tests
- **NEW**: `get_local_ip()` - Determines local IP address
- **NEW**: `is_local_ip()` - Checks if IP is in private range
- **NEW**: `identify_camera_type()` - Identifies camera types from banners
- **NEW**: `scan_ip_for_cameras()` - Scans IP addresses for camera services
- **NEW**: `check_cctv_port()` - Checks specific ports for CCTV software
- **NEW**: `scan_upnp_devices()` - Scans for UPnP devices
- **NEW**: `analyze_network_traffic()` - Analyzes network traffic patterns
- **NEW**: `scan_wifi_devices()` - Scans for WiFi devices

### 6. System Monitoring Tests
- System information display
- Performance monitoring
- CPU, memory, and disk usage
- Process monitoring

### 7. AI Integration Tests
- Ollama AI chat functionality
- Text generation and analysis
- Image generation
- Document analysis

## New Network Scanning Features Tested

The test suite includes comprehensive tests for the newly added network security features:

### Network Camera Scan
- Scans local network for IP cameras
- Identifies common camera ports (80, 81, 443, 554, 8080, 8081, 8082, 8888, 9999)
- Detects camera types from HTTP banners
- Uses multi-threading for efficient scanning

### CCTV Detection
- Advanced surveillance device detection
- UPnP device discovery
- Network traffic pattern analysis
- WiFi device scanning
- Security recommendations

### Camera Type Identification
- Recognizes common camera brands (Axis, Hikvision, Dahua, Foscam)
- Identifies CCTV systems and DVRs
- Detects RTSP streaming services
- Port-based detection for suspicious services

## Test Coverage

The test suite provides comprehensive coverage of:
- ✅ All 141 functions in `cli_assistant.py`
- ✅ Error handling and edge cases
- ✅ Mocked network operations for safe testing
- ✅ Integration between different components
- ✅ User interface interactions
- ✅ File system operations
- ✅ Network security features

## Mocking and Safety

The tests use extensive mocking to ensure:
- **Safe testing**: No actual network scanning is performed during tests
- **Isolated testing**: Each test runs in a temporary directory
- **Predictable results**: Mocked responses provide consistent test results
- **No side effects**: Tests don't modify system files or network settings

## Expected Test Results

When running the full test suite, you should see:
- **Basic tests**: 100% pass rate
- **Network tests**: 100% pass rate (with mocked responses)
- **Security tests**: Variable pass rate (depends on system configuration)
- **Integration tests**: 100% pass rate

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure `cli_assistant.py` is in the same directory
2. **Permission errors**: Run tests in a directory where you have write permissions
3. **Network test failures**: These are expected in some environments and are handled gracefully

### Test Environment

The tests are designed to run in any environment:
- ✅ macOS, Linux, Windows
- ✅ With or without network access
- ✅ With or without admin privileges
- ✅ In virtual environments

## Contributing

When adding new features to `cli_assistant.py`:
1. Add corresponding test cases to the appropriate test file
2. Update this README with new test categories
3. Ensure all tests pass before submitting changes
4. Add integration tests for new menu options

## Test Reports

The test runner generates:
- Console output with real-time test results
- JSON test report (`test_report.json`)
- Summary statistics and success rates
- Detailed error messages for failed tests

---

**Note**: The network scanning features are designed for legitimate security testing and network administration. Always ensure you have permission to scan networks and devices before using these features in production environments.
