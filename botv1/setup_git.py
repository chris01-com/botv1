
#!/usr/bin/env python3
import subprocess
import os

def setup_git():
    """Initialize git repository and set up for auto-commits"""
    try:
        # Check if git is already initialized
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Initializing git repository...")
            subprocess.run(['git', 'init'], check=True)
            
            # Set up basic git config if not set
            try:
                subprocess.run(['git', 'config', 'user.name'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                subprocess.run(['git', 'config', 'user.name', 'Quest Bot'], check=True)
                
            try:
                subprocess.run(['git', 'config', 'user.email'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                subprocess.run(['git', 'config', 'user.email', 'bot@example.com'], check=True)
            
            print("Git repository initialized!")
        else:
            print("Git repository already exists.")
            
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Add .gitignore if it doesn't exist
        if not os.path.exists('.gitignore'):
            print("Creating .gitignore...")
            with open('.gitignore', 'w') as f:
                f.write("__pycache__/\n*.pyc\n!data/\n")
        
        print("Git setup complete!")
        print("To connect to GitHub:")
        print("1. Create a new repository on GitHub")
        print("2. Run: git remote add origin <your-repo-url>")
        print("3. Run: git push -u origin main")
        
    except subprocess.CalledProcessError as e:
        print(f"Error setting up git: {e}")
        print("Make sure git is installed on your system.")

if __name__ == "__main__":
    setup_git()
