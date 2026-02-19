
import subprocess
import sys

def run_tests():
    result = subprocess.run([sys.executable, "-m", "pytest", "-v"], capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    with open("full_test_output.txt", "w", encoding="utf-8") as f:
        f.write(result.stdout)
        f.write("\nSTDERR:\n")
        f.write(result.stderr)

if __name__ == "__main__":
    run_tests()
