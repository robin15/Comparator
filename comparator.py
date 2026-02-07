import hashlib
import os
import sys

try:
    import msvcrt
except ImportError:
    msvcrt = None

class BinaryComparator:
    @staticmethod
    def compare(path1, path2):
        if os.path.getsize(path1) != os.path.getsize(path2):
            return {"match": False, "reason": "Size differs"}

        sha256 = hashlib.sha256()
        with open(path1, "rb") as f1, open(path2, "rb") as f2:
            while chunk := f1.read(4096):
                sha256.update(chunk)
            hash1 = sha256.hexdigest()

            sha256_2 = hashlib.sha256()
            while chunk := f2.read(4096):
                sha256_2.update(chunk)
            hash2 = sha256_2.hexdigest()

        if hash1 == hash2:
            return {"match": True, "reason": "Full match (SHA256)"}
        else:
            return {"match": False, "reason": "Binary data differs"}

class ImageComparatorApp:
    GOLDEN_DIR = "./golden"

    def __init__(self):
        self.results = []

    def run(self):
        print("=== Binary Image Comparison Tool (Python version) ===")
        if not os.path.exists(self.GOLDEN_DIR):
            print(f"Error: '{self.GOLDEN_DIR}' directory not found.")
            self.wait_for_any_key()
            return

        files = [f for f in os.listdir(self.GOLDEN_DIR) if f.endswith('.bin')]
        
        if not files:
            print(f"No .bin files found in {self.GOLDEN_DIR}.")
            self.wait_for_any_key()
            return

        for filename in files:
            golden_path = os.path.join(self.GOLDEN_DIR, filename)
            target_path = os.path.join(".", filename)

            print(f"Comparing {filename:30s}", end="")

            if os.path.exists(target_path):
                result = BinaryComparator.compare(golden_path, target_path)
                if result["match"]:
                    print("[MATCH]")
                    self.results.append({"file": filename, "status": "MATCH"})
                else:
                    print(f"[MISMATCH] ({result['reason']})")
                    self.results.append({"file": filename, "status": "MISMATCH"})
            else:
                print("[SKIP] (Not found)")
                self.results.append({"file": filename, "status": "SKIP"})

        self.print_summary()

    def print_summary(self):
        print("\n" + "="*40)
        print("Summary:")
        mismatch_count = 0
        for r in self.results:
            print(f"{r['status']:10}: {r['file']}")
            if r['status'] == "MISMATCH":
                mismatch_count += 1
        
        print("\n" + "-"*40)
        self.wait_for_any_key()
        sys.exit(1 if mismatch_count > 0 else 0)

    def wait_for_any_key(self):
        """Any Keyで終了するための待機処理"""
        print("Press any key to exit...")
        if msvcrt:
            msvcrt.getch()
        else:
            input()

if __name__ == "__main__":
    ImageComparatorApp().run()