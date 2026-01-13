"""
Script hỗ trợ setup nhanh cho SWOT AI Analyzer
"""
import os
import sys

def check_dependencies():
    """Kiểm tra các dependencies cần thiết"""
    print("🔍 Đang kiểm tra dependencies...")
    
    required_packages = [
        'streamlit',
        'pandas',
        'openpyxl',
        'google.generativeai',
        'dotenv',
        'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'google.generativeai':
                __import__('google.generativeai')
            elif package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - CHƯA CÀI ĐẶT")
            missing_packages.append(package)
    
    if missing_packages:
        print("\n⚠️  Thiếu một số packages. Chạy lệnh sau để cài đặt:")
        print("   pip install -r requirements.txt")
        return False
    
    print("\n✅ Tất cả dependencies đã được cài đặt!")
    return True


def check_env_file():
    """Kiểm tra file .env"""
    print("\n🔍 Đang kiểm tra file .env...")
    
    if os.path.exists('.env'):
        print("  ✅ File .env đã tồn tại")
        
        # Kiểm tra API key
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key and api_key != 'your_gemini_api_key_here':
            print("  ✅ GEMINI_API_KEY đã được cấu hình")
            return True
        else:
            print("  ⚠️  GEMINI_API_KEY chưa được cấu hình hoặc đang dùng giá trị mẫu")
            print("     Vui lòng mở file .env và thêm API key của bạn")
            return False
    else:
        print("  ❌ File .env chưa tồn tại")
        print("     Tạo file .env từ .env.example...")
        
        if os.path.exists('.env.example'):
            with open('.env.example', 'r') as f:
                content = f.read()
            
            with open('.env', 'w') as f:
                f.write(content)
            
            print("  ✅ Đã tạo file .env")
            print("  ⚠️  Vui lòng mở file .env và thêm GEMINI_API_KEY của bạn")
            print("     Lấy API key tại: https://makersuite.google.com/app/apikey")
            return False
        else:
            print("  ❌ Không tìm thấy file .env.example")
            return False


def main():
    """Hàm chính"""
    print("=" * 50)
    print("🚀 SWOT AI Analyzer - Setup Check")
    print("=" * 50)
    
    deps_ok = check_dependencies()
    env_ok = check_env_file()
    
    print("\n" + "=" * 50)
    if deps_ok and env_ok:
        print("✅ Setup hoàn tất! Bạn có thể chạy ứng dụng bằng:")
        print("   streamlit run app.py")
    else:
        print("⚠️  Vui lòng hoàn tất các bước còn thiếu ở trên")
    print("=" * 50)


if __name__ == "__main__":
    main()
