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
        # 1. サイズチェック
        size1 = os.path.getsize(path1)
        size2 = os.path.getsize(path2)
        if size1 != size2:
            return {"match": False, "reason": f"Size differs (G:{size1} bytes / T:{size2} bytes)"}

        # 2. SHA256ハッシュチェック (高速な全体一致確認)
        with open(path1, "rb") as f1, open(path2, "rb") as f2:
            # ハッシュ計算用のループ
            hash1 = BinaryComparator._calculate_sha256(f1)
            hash2 = BinaryComparator._calculate_sha256(f2)

            if hash1 == hash2:
                return {"match": True, "reason": "Full match (SHA256)"}

            # 3. 画素値（詳細バイナリ）比較
            # SHA256が不一致の場合、先頭から1バイトずつ比較して不一致箇所を特定する
            f1.seek(0)
            f2.seek(0)
            offset = 0
            chunk_size = 4096
            
            while True:
                b1 = f1.read(chunk_size)
                b2 = f2.read(chunk_size)
                if not b1:
                    break
                
                if b1 != b2:
                    # チャンク内で不一致がある場合、その詳細な位置を特定
                    for i in range(len(b1)):
                        if b1[i] != b2[i]:
                            addr = offset + i
                            return {
                                "match": False, 
                                "reason": f"Pixel data mismatch at address: 0x{addr:X} (G:0x{b1[i]:02X} != T:0x{b2[i]:02X})"
                            }
                offset += len(b1)

        return {"match": False, "reason": "Unknown error during comparison"}

    @staticmethod
    def _calculate_sha256(file_handle):
        sha256 = hashlib.sha256()
        file_handle.seek(0)
        while chunk := file_handle.read(4096):
            sha256.update(chunk)
        return sha256.hexdigest()

class ImageComparatorApp:
    GOLDEN_DIR = "./golden"

    def __init__(self):
        self.results = []

    def run(self):
        print("=== Binary Image Comparison Tool (Detailed mode) ===")
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

            print(f"Comparing {filename:30s} ", end="", flush=True)

            if os.path.exists(target_path):
                result = BinaryComparator.compare(golden_path, target_path)
                if result["match"]:
                    print("[MATCH]")
                    self.results.append({"file": filename, "status": "MATCH"})
                else:
                    print(f"[MISMATCH]")
                    print(f"  └─ Reason: {result['reason']}")
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
        print("Press any key to exit...")
        if msvcrt:
            msvcrt.getch()
        else:
            input()

if __name__ == "__main__":
    ImageComparatorApp().run()
