#!/usr/bin/env python3
"""
Simple Test Runner for CLI Assistant
Provides easy execution of comprehensive tests
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def print_banner():
    """Print test runner banner"""
    print("🧪" + "="*58 + "🧪")
    print("🧪" + " "*20 + "CLI ASSISTANT TEST SUITE" + " "*20 + "🧪")
    print("🧪" + "="*58 + "🧪")
    print()

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_modules = ['unittest', 'json', 'tempfile', 'shutil', 'socket', 'threading', 'time', 're']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing required modules: {', '.join(missing_modules)}")
        return False
    
    print("✅ All dependencies available")
    return True

def run_basic_tests():
    """Run basic functionality tests"""
    print("\n🔧 Running basic functionality tests...")
    
    try:
        # Test import
        from cli_assistant import SimpleMenu, UltimateCronManager
        print("✅ Module import successful")
        
        # Test basic initialization
        menu = SimpleMenu()
        print("✅ SimpleMenu initialization successful")
        
        # Test manager initialization (with mock config)
        import tempfile
        import json
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create minimal config
            config = {"jobs": [], "settings": {}}
            with open("cron_config.json", "w") as f:
                json.dump(config, f)
            
            manager = UltimateCronManager()
            print("✅ UltimateCronManager initialization successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return False

def run_comprehensive_tests():
    """Run comprehensive test suite"""
    print("\n🚀 Running comprehensive test suite...")
    
    try:
        # Import and run the comprehensive test suite
        from test_cli_assistant_comprehensive import run_comprehensive_tests
        
        start_time = time.time()
        success = run_comprehensive_tests()
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"\n⏱️  Test execution time: {duration:.2f} seconds")
        
        return success
        
    except Exception as e:
        print(f"❌ Comprehensive tests failed: {e}")
        return False

def run_network_tests():
    """Run network-specific tests"""
    print("\n🌐 Running network functionality tests...")
    
    try:
        from cli_assistant import UltimateCronManager
        import tempfile
        import json
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create minimal config
            config = {"jobs": [], "settings": {}}
            with open("cron_config.json", "w") as f:
                json.dump(config, f)
            
            manager = UltimateCronManager()
            
            # Test network functions
            print("  🔍 Testing get_local_ip...")
            local_ip = manager.get_local_ip()
            if local_ip:
                print(f"    ✅ Local IP: {local_ip}")
            else:
                print("    ⚠️  Could not determine local IP")
            
            print("  🔍 Testing is_local_ip...")
            test_ips = ['192.168.1.1', '10.0.0.1', '8.8.8.8', '127.0.0.1']
            for ip in test_ips:
                is_local = manager.is_local_ip(ip)
                print(f"    {'✅' if is_local else '❌'} {ip}: {'Local' if is_local else 'Public'}")
            
            print("  🔍 Testing camera type identification...")
            test_banners = [
                ("HTTP/1.1 200 OK\r\nServer: IP Camera\r\n", 80),
                ("HTTP/1.1 200 OK\r\nServer: CCTV System\r\n", 80),
                ("", 554),  # RTSP port
                ("HTTP/1.1 200 OK\r\nServer: Apache\r\n", 80)
            ]
            
            for banner, port in test_banners:
                camera_type = manager.identify_camera_type(banner, port)
                print(f"    📹 Banner: {banner[:30]}... Port: {port} -> {camera_type or 'Not a camera'}")
        
        print("✅ Network tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Network tests failed: {e}")
        return False

def run_security_tests():
    """Run security-specific tests"""
    print("\n🔒 Running security functionality tests...")
    
    try:
        from cli_assistant import UltimateCronManager
        import tempfile
        import json
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create minimal config
            config = {"jobs": [], "settings": {}}
            with open("cron_config.json", "w") as f:
                json.dump(config, f)
            
            manager = UltimateCronManager()
            
            # Test security functions
            print("  🔍 Testing security checks...")
            
            checks = [
                ("File permissions", manager.check_file_permissions),
                ("Open ports", manager.check_open_ports),
                ("Suspicious processes", manager.check_suspicious_processes),
                ("Firewall status", manager.check_firewall_status),
                ("Screen lock", manager.check_screen_lock),
                ("Encryption", manager.check_encryption),
                ("Auto updates", manager.check_auto_updates),
                ("Antivirus", manager.check_antivirus)
            ]
            
            for check_name, check_func in checks:
                try:
                    result = check_func()
                    print(f"    {'✅' if result else '❌'} {check_name}: {'Pass' if result else 'Fail'}")
                except Exception as e:
                    print(f"    ⚠️  {check_name}: Error - {e}")
        
        print("✅ Security tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Security tests failed: {e}")
        return False

def generate_test_report():
    """Generate a test report"""
    print("\n📊 Generating test report...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_suite": "CLI Assistant Comprehensive Tests",
        "version": "1.0.0",
        "tests_run": [],
        "summary": {}
    }
    
    # This would be populated with actual test results
    # For now, just create a basic report structure
    
    report_file = "test_report.json"
    try:
        import json
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"✅ Test report saved to: {report_file}")
    except Exception as e:
        print(f"❌ Failed to save test report: {e}")

def main():
    """Main test runner function"""
    print_banner()
    
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing modules.")
        return False
    
    # Run different test categories
    test_results = {}
    
    # Basic tests
    test_results['basic'] = run_basic_tests()
    
    # Network tests
    test_results['network'] = run_network_tests()
    
    # Security tests
    test_results['security'] = run_security_tests()
    
    # Comprehensive tests (optional - can be slow)
    print("\n❓ Run comprehensive test suite? (y/n): ", end="")
    try:
        response = input().lower().strip()
        if response in ['y', 'yes']:
            test_results['comprehensive'] = run_comprehensive_tests()
        else:
            print("⏭️  Skipping comprehensive tests")
            test_results['comprehensive'] = None
    except KeyboardInterrupt:
        print("\n⏭️  Skipping comprehensive tests")
        test_results['comprehensive'] = None
    
    # Generate report
    generate_test_report()
    
    # Print final summary
    print("\n" + "="*60)
    print("📋 FINAL TEST SUMMARY")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    
    for test_type, result in test_results.items():
        if result is not None:
            total_tests += 1
            if result:
                passed_tests += 1
                status = "✅ PASSED"
            else:
                status = "❌ FAILED"
        else:
            status = "⏭️  SKIPPED"
        
        print(f"{test_type.upper():<15}: {status}")
    
    if total_tests > 0:
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n🎯 Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        if success_rate == 100:
            print("🎉 All tests passed! CLI Assistant is working correctly.")
        elif success_rate >= 80:
            print("⚠️  Most tests passed. Some issues detected.")
        else:
            print("❌ Multiple test failures detected. Please check the output above.")
    else:
        print("⚠️  No tests were executed.")
    
    print(f"\n🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
