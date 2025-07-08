#!/usr/bin/env python3
"""
Test script to verify Billfrog package structure.
This tests basic imports and structure without external dependencies.
"""

def test_basic_imports():
    """Test basic package imports."""
    print("🔍 Testing basic package imports...")
    
    try:
        # Test version import
        from billfrog import __version__, __author__
        print(f"✅ Package version: {__version__}")
        print(f"✅ Package author: {__author__}")
        
        # Test individual module existence (without importing dependencies)
        import os
        import sys
        
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Check that all module files exist
        expected_files = [
            "billfrog/__init__.py",
            "billfrog/config.py",
            "billfrog/cli.py",
            "billfrog/ai_providers/__init__.py",
            "billfrog/ai_providers/openai_provider.py",
            "billfrog/email/__init__.py",
            "billfrog/email/sender.py",
            "billfrog/receipts/__init__.py",
            "billfrog/receipts/generator.py",
            "billfrog/scheduler/__init__.py",
            "billfrog/scheduler/task_scheduler.py",
            "billfrog/storage/__init__.py",
            "billfrog/storage/database.py",
        ]
        
        for file_path in expected_files:
            if os.path.exists(file_path):
                print(f"✅ Found: {file_path}")
            else:
                print(f"❌ Missing: {file_path}")
                return False
        
        # Check packaging files
        packaging_files = [
            "pyproject.toml",
            "requirements.txt",
            "README.md",
            "LICENSE",
            "MANIFEST.in"
        ]
        
        for file_path in packaging_files:
            if os.path.exists(file_path):
                print(f"✅ Found packaging file: {file_path}")
            else:
                print(f"❌ Missing packaging file: {file_path}")
        
        print("\n🎉 Basic package structure test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_package_metadata():
    """Test package metadata."""
    print("\n📦 Testing package metadata...")
    
    try:
        # Read pyproject.toml
        with open("pyproject.toml", "r") as f:
            content = f.read()
            
        required_sections = [
            "[build-system]",
            "[project]",
            "name = \"billfrog\"",
            "version = \"0.1.0\"",
            "billfrog = \"billfrog.cli:main\""
        ]
        
        for section in required_sections:
            if section in content:
                print(f"✅ Found in pyproject.toml: {section}")
            else:
                print(f"❌ Missing in pyproject.toml: {section}")
                return False
        
        # Check requirements.txt
        with open("requirements.txt", "r") as f:
            requirements = f.read()
            
        required_deps = [
            "typer",
            "rich", 
            "openai",
            "supabase",
            "jinja2",
            "schedule",
            "cryptography"
        ]
        
        for dep in required_deps:
            if dep in requirements:
                print(f"✅ Found dependency: {dep}")
            else:
                print(f"❌ Missing dependency: {dep}")
                return False
        
        print("✅ Package metadata test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Metadata test failed: {e}")
        return False

def test_examples():
    """Test example files."""
    print("\n📝 Testing example files...")
    import os
    
    example_files = [
        "examples/basic_usage.py",
        "examples/custom_receipt.py",
        "examples/supabase_setup.md"
    ]
    
    for file_path in example_files:
        if os.path.exists(file_path):
            print(f"✅ Found example: {file_path}")
        else:
            print(f"❌ Missing example: {file_path}")
            return False
    
    print("✅ Example files test passed!")
    return True

def main():
    """Run all tests."""
    print("🐸 Billfrog Package Structure Test")
    print("=" * 40)
    
    tests = [
        test_basic_imports,
        test_package_metadata,
        test_examples
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Package structure looks good.")
        print("\n📦 Ready for installation with:")
        print("   pip install -e .")
        print("   # or")
        print("   pip install billfrog")
    else:
        print("❌ Some tests failed. Please check the package structure.")
    
    return passed == total

if __name__ == "__main__":
    main()