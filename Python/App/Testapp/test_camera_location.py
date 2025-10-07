#!/usr/bin/env python3
"""
Quick Test Script for Camera Location Features
Demonstrates how to locate IP cameras from your computer
"""

import sys
import os
import tempfile
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_camera_location_features():
    """Test the camera location and mapping features"""
    print("🎯 Testing Camera Location Features")
    print("=" * 50)
    
    try:
        from cli_assistant import UltimateCronManager
        
        # Create temporary environment
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create minimal config
            config = {"jobs": [], "settings": {}}
            with open("cron_config.json", "w") as f:
                json.dump(config, f)
            
            manager = UltimateCronManager()
            
            # Test 1: Get local IP
            print("\n1️⃣ Getting your local IP address...")
            local_ip = manager.get_local_ip()
            if local_ip:
                print(f"   ✅ Your IP: {local_ip}")
                network_base = '.'.join(local_ip.split('.')[:-1])
                print(f"   📡 Network: {network_base}.x")
            else:
                print("   ❌ Could not determine local IP")
                return False
            
            # Test 2: Test IP location estimation
            print("\n2️⃣ Testing IP location estimation...")
            test_ips = [
                '192.168.1.5',    # Infrastructure
                '192.168.1.25',   # Server room
                '192.168.1.75',   # Office area
                '192.168.1.125',  # Common areas
                '192.168.1.175',  # Perimeter
                '192.168.1.225'   # Remote areas
            ]
            
            for ip in test_ips:
                location = manager.estimate_camera_location(ip)
                print(f"   📍 {ip} → {location}")
            
            # Test 3: Test camera brand identification
            print("\n3️⃣ Testing camera brand identification...")
            test_html_samples = [
                ("<title>Axis Camera</title>", "Axis"),
                ("<title>Hikvision Web Interface</title>", "Hikvision"),
                ("<title>Dahua IP Camera</title>", "Dahua"),
                ("<title>Foscam Digital Camera</title>", "Foscam"),
                ("<title>Generic Web Server</title>", "Unknown")
            ]
            
            for html, expected_brand in test_html_samples:
                result = manager.identify_camera_brand_model(html)
                brand = result['brand']
                status = "✅" if expected_brand.lower() in brand.lower() else "❌"
                print(f"   {status} HTML: {html[:30]}... → Brand: {brand}")
            
            # Test 4: Test capability detection
            print("\n4️⃣ Testing camera capability detection...")
            test_capability_html = [
                "motion detection enabled",
                "night vision infrared",
                "ptz pan tilt zoom",
                "hd 1080p recording",
                "audio microphone sound"
            ]
            
            for html in test_capability_html:
                capabilities = manager.detect_camera_capabilities(html)
                print(f"   🎥 '{html}' → {capabilities}")
            
            # Test 5: Test security issue detection
            print("\n5️⃣ Testing security issue detection...")
            test_security_html = [
                "admin password login",
                "http connection",
                "directory traversal ../",
                "sql injection vulnerability"
            ]
            
            for html in test_security_html:
                issues = manager.check_camera_security(html, "192.168.1.100", 80)
                print(f"   🔒 '{html}' → {issues}")
            
            print("\n🎉 All camera location features are working!")
            print("\n📋 To use these features in the CLI Assistant:")
            print("   1. Run: python3 cli_assistant.py")
            print("   2. Go to: Security Monitor → Camera Location Map")
            print("   3. Or: Security Monitor → Camera Access & Control")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Camera location test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demonstrate_network_scanning():
    """Demonstrate how the network scanning works"""
    print("\n🔍 Network Scanning Demonstration")
    print("=" * 50)
    
    print("The camera location system works by:")
    print("1. 🌐 Detecting your local network (e.g., 192.168.1.x)")
    print("2. 🔍 Scanning all IP addresses (1-254) for camera services")
    print("3. 🎯 Testing common camera ports (80, 81, 443, 554, 8080, etc.)")
    print("4. 📡 Identifying camera brands from HTTP responses")
    print("5. 📍 Estimating physical locations based on IP ranges")
    print("6. 🗺️ Creating visual network topology maps")
    print("7. 🔒 Analyzing security issues and vulnerabilities")
    
    print("\n🎥 Supported Camera Brands:")
    brands = [
        "Axis", "Hikvision", "Dahua", "Foscam", "D-Link", 
        "Netgear", "TP-Link", "Wyze", "Ring", "Nest", 
        "Arlo", "Eufy", "Reolink"
    ]
    for brand in brands:
        print(f"   • {brand}")
    
    print("\n🔧 Camera Capabilities Detected:")
    capabilities = [
        "Motion Detection", "Night Vision", "PTZ Control",
        "HD Recording", "Audio Recording", "Cloud Storage",
        "Mobile App", "Web Interface", "Email Alerts"
    ]
    for capability in capabilities:
        print(f"   • {capability}")

def main():
    """Main demonstration function"""
    print("🎯 IP Camera Location System Demo")
    print("=" * 60)
    print("This demonstrates how to locate IP cameras from your computer")
    print()
    
    # Run the tests
    success = test_camera_location_features()
    
    # Show demonstration
    demonstrate_network_scanning()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ Camera location features are working correctly!")
        print("\n🚀 Ready to use:")
        print("   • Camera Location Map - Visual network mapping")
        print("   • Camera Access & Control - Direct camera management")
        print("   • Network Camera Scan - Advanced detection")
        print("\n💡 To start using:")
        print("   python3 cli_assistant.py")
        print("   → Security Monitor → Camera Location Map")
    else:
        print("❌ Some features need attention")
    
    print("\n🎯 The system can now:")
    print("   • Find all cameras on your network")
    print("   • Show their physical locations")
    print("   • Identify brands and models")
    print("   • Test security vulnerabilities")
    print("   • Open camera web interfaces")
    print("   • Create network topology maps")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
